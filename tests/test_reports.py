from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from unittest import mock
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliability.model import load_report, normalize_rows, validate_matches, timestamp, sha256, child
from reliability.publisher import build_report, check_destination, render_html
from helpers import row


class DataTests(unittest.TestCase):
    def setUp(self):
        self.cutoff = timestamp("2026-09-30T00:00:00Z")

    def validate(self, rows, groups=("Total",)):
        return normalize_rows(rows, list(groups), self.cutoff, annual=True)

    def test_openai_regression_input(self):
        report = load_report(ROOT / "configs/openai-2026-09-27-v1.1.json")
        self.assertEqual(len(report.annual), 24)
        self.assertEqual(len(report.matched), 8)
        self.assertEqual([r["incident_count"] for r in report.annual if r["group"] == "Overall"], [10,43,172,187,339,255])
        self.assertEqual(sha256(report.data_bytes), "a6076510b063149e2bdf659395caf294addfad060507f94500601be72ccd2b5f")

    def test_different_company_years_and_groups(self):
        report = load_report(ROOT / "configs/example-provider.json")
        self.assertEqual(report.company, "ExampleAI")
        self.assertEqual(report.years, [2022,2023,2024])
        self.assertNotIn(2023, {r["year"] for r in report.annual})
        self.assertEqual([g["id"] for g in report.groups], ["Total","Inference","Console"])

    def test_arbitrary_group_count(self):
        groups = [f"Service-{n}" for n in range(17)]
        self.assertEqual(len(self.validate([row(2020,g) for g in groups], groups)), 17)

    def test_duplicate_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            self.validate([row(2020,"Total"),row(2020,"Total")])

    def test_unknown_group_rejected(self):
        with self.assertRaisesRegex(ValueError,"Unconfigured"):
            self.validate([row(2020,"Unknown")])

    def test_missing_year_is_not_created_as_zero(self):
        self.assertEqual([r["year"] for r in self.validate([row(2018,"Total"),row(2020,"Total")])], [2018,2020])

    def test_inactive_is_null(self):
        result = self.validate([{"year":2020,"group":"Total","incident_count":None,"denominator_seconds":0}])[0]
        self.assertIsNone(result["incident_count"])
        self.assertIsNone(result["incidents_per_30_days"])

    def test_inactive_cannot_be_100_percent(self):
        with self.assertRaises(ValueError):
            self.validate([{"year":2020,"group":"Total","incident_count":None,"availability_all":1}])

    def test_zero_incidents_is_valid_observed_data(self):
        result = self.validate([row(2020,"Total",0,(0,0,0))])[0]
        self.assertEqual(result["availability_all"],1)
        self.assertEqual(result["incidents_per_30_days"],0)

    def test_leap_year_denominator(self):
        self.assertEqual(self.validate([row(2024,"Total")])[0]["observation_days"],366)

    def test_partial_year_in_any_position(self):
        record = row(2020,"Total",start="2020-03-02T00:00:00Z")
        self.assertTrue(self.validate([record])[0]["partial_year"])

    def test_wrong_partial_flag_rejected(self):
        record = row(2020,"Total");record["partial_year"] = True
        with self.assertRaisesRegex(ValueError,"partial_year"):
            self.validate([record])

    def test_timestamp_needs_timezone(self):
        with self.assertRaisesRegex(ValueError,"timezone"):
            timestamp("2020-01-01T00:00:00")

    def test_future_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"cutoff"):
            self.validate([row(2026,"Total")])

    def test_wrong_year_window_rejected(self):
        record = row(2020,"Total");record["year"] = 2021
        with self.assertRaisesRegex(ValueError,"specified UTC year"):
            self.validate([record])

    def test_invalid_numbers_rejected(self):
        for bad in (-1,float("nan"),float("inf"),"10",True,2.5):
            with self.subTest(bad=bad):
                record=row(2020,"Total");record["incident_count"]=bad
                with self.assertRaises(ValueError):
                    self.validate([record])

    def test_denominator_mismatch_rejected(self):
        record=row(2020,"Total");record["denominator_seconds"]=1
        with self.assertRaisesRegex(ValueError,"denominator"):
            self.validate([record])

    def test_downtime_union_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"downtime"):
            self.validate([row(2020,"Total",hours=(3,1,2))])

    def test_percent_instead_of_ratio_rejected(self):
        record=row(2020,"Total");record["availability_all"]=99.9
        with self.assertRaisesRegex(ValueError,"ratio"):
            self.validate([record])

    def test_inconsistent_availability_rejected(self):
        record=row(2020,"Total");record["availability_all"]=0.8
        with self.assertRaises(ValueError):
            self.validate([record])

    def test_frequency_derived_without_mutating_input(self):
        record=row(2020,"Total");before=deepcopy(record)
        result=self.validate([record])[0]
        self.assertAlmostEqual(result["incidents_per_30_days"],10*30/366)
        self.assertEqual(record,before)

    def test_matched_calendar_windows(self):
        rows=[row(y,"Total",end=f"{y}-07-01T00:00:00Z",matched=True) for y in (2020,2021)]
        validate_matches(rows)  # Leap years may have different durations but matching dates.

    def test_mismatched_calendar_windows_rejected(self):
        rows=[row(y,"Total",end=f"{y}-07-0{y-2019}T00:00:00Z",matched=True) for y in (2020,2021)]
        with self.assertRaisesRegex(ValueError,"matched windows"):
            validate_matches(rows)

    def test_mismatched_count_basis_rejected(self):
        rows=[row(y,"Total",end=f"{y}-07-01T00:00:00Z",matched=True) for y in (2020,2021)]
        rows[1]["count_basis"]="first_impact"
        with self.assertRaises(ValueError):
            validate_matches(rows)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.report=load_report(ROOT / "configs/example-provider.json")
        self.report.markdown_bytes=b"# Test report\n\n## Analysis\n\nFrozen data.\n"

    def tearDown(self):
        self.temp.cleanup()

    def build(self, **kwargs):
        with mock.patch("reliability.publisher.render_charts", return_value=[]):
            return build_report(self.report,self.root/"out",**kwargs)

    def test_build_preserves_input_and_packages_portable_config(self):
        before=self.report.data_path.read_bytes()
        result=self.build()
        dest=self.root/"out"
        self.assertEqual((dest/(self.report.stem+".md")).read_bytes(),self.report.markdown_bytes)
        self.assertEqual((dest/"trend_data.json").read_bytes(),before)
        self.assertEqual(self.report.data_path.read_bytes(),before)
        portable=load_report(dest/"report.config.json")
        self.assertEqual(portable.company,"ExampleAI")
        with zipfile.ZipFile(dest/result["archive"]) as archive:
            self.assertIn("tools/publish_report.py",archive.namelist())
            self.assertIn("tools/reliability/model.py",archive.namelist())
            self.assertIn("requirements.txt",archive.namelist())
        manifest=json.loads((dest/"publication_manifest.json").read_text())
        self.assertFalse(manifest["statistics_reclassified_or_refreshed"])
        self.assertTrue(manifest["synthetic"])

    def test_no_company_leakage_in_example_html(self):
        self.build()
        body=(self.root/"out"/(self.report.stem+"_github.html")).read_text()
        self.assertIn("合成示例数据",body)
        self.assertNotIn("OpenAI",body)

    def test_bad_hash_does_not_repair_input(self):
        cfg=deepcopy(self.report.config)
        cfg["inputs"]={"markdown":str(self.report.markdown_path),"data":str(self.report.data_path)}
        cfg["integrity"]["data_sha256"]="0"*64
        path=self.root/"config.json";path.write_text(json.dumps(cfg))
        before=self.report.data_path.read_bytes()
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            load_report(path)
        self.assertEqual(before,self.report.data_path.read_bytes())

    def test_rebuild_refuses_existing_without_flag(self):
        self.build()
        with self.assertRaisesRegex(ValueError,"non-empty"):
            self.build()

    def test_rebuild_only_owned_output(self):
        self.build(); self.build(overwrite=True)
        (self.root/"out"/"personal.txt").write_text("do not remove")
        with self.assertRaisesRegex(ValueError,"Unmanaged"):
            self.build(overwrite=True)
        self.assertTrue((self.root/"out"/"personal.txt").is_file())

    def test_refuses_source_directory(self):
        with self.assertRaisesRegex(ValueError,"input file"):
            check_destination(self.report,self.report.data_path.parent,True)

    def test_refuses_configured_symlink_output(self):
        target=self.root/"target";target.mkdir()
        link=self.root/"link";link.symlink_to(target,target_is_directory=True)
        self.report.config["output"]["directory"]=str(link)
        with self.assertRaisesRegex(ValueError,"symlink"):
            build_report(self.report)

    def test_refuses_unknown_directory(self):
        out=self.root/"out";out.mkdir();(out/"file.txt").write_text("private")
        with self.assertRaisesRegex(ValueError,"unowned"):
            self.build(overwrite=True)

    def test_refuses_symlink_output(self):
        target=self.root/"target";target.mkdir()
        (self.root/"out").symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"symlink"):
            self.build()

    def test_failure_leaves_previous_generation_intact(self):
        self.build()
        old=(self.root/"out"/"publication_manifest.json").read_bytes()
        with mock.patch("reliability.publisher.render_charts",side_effect=ValueError("bad chart")):
            with self.assertRaises(ValueError):
                build_report(self.report,self.root/"out",overwrite=True)
        self.assertEqual(old,(self.root/"out"/"publication_manifest.json").read_bytes())
        self.assertFalse(list(self.root.glob(".reliability-build-*")))

    def test_refuses_path_traversal(self):
        for value in ("../secret.png","/tmp/secret.png",r"..\secret.png","https://other.test/p.png"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    child(self.root,value)

    def test_refuses_remote_images(self):
        self.report.markdown_bytes=b"![external](https://example.com/p.png)"
        with self.assertRaisesRegex(ValueError,"local relative"):
            render_html(self.report,self.root)

    def test_refuses_encoded_traversal(self):
        self.report.markdown_bytes=b"![bad](%2e%2e/secret.png)"
        with self.assertRaises(ValueError):
            render_html(self.report,self.root)

    def test_html_escapes_raw_scripts_and_title(self):
        self.report.markdown_bytes=b"# Hello\n<script>alert(1)</script>"
        self.report.config["report"]["title"]="<script>alert(1)</script>"
        body=render_html(self.report,self.root)
        self.assertNotIn("<script>",body)
        self.assertIn("&lt;script&gt;",body)

    def test_html_embeds_local_images(self):
        self.report.markdown_bytes=b"![figure](charts/a.svg)"
        folder=self.root/"charts";folder.mkdir()
        for name in ("a.svg","a_mobile.svg"):
            (folder/name).write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        result=render_html(self.report,self.root)
        self.assertIn("<picture>",result)
        self.assertIn("data:image/svg+xml;base64,",result)

    def test_cli_validation_no_output(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/publish_report.py"),"--config",str(ROOT/"configs/example-provider.json"),"--output",str(self.root/"unused"),"--validate-only"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.root/"unused").exists())

    def test_imports_have_no_cli_or_build_side_effect(self):
        for name in ("publish_report","render_trends"):
            spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
