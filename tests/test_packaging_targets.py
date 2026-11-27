"""Offline tests for distribution selection and package version isolation."""
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingTargetsTest(unittest.TestCase):
    def select(self, **values):
        env = {k: v for k, v in os.environ.items() if k not in (
            'ID', 'ID_LIKE', 'VERSION_CODENAME', 'UBUNTU_CODENAME', 'DEBIAN_CODENAME')}
        env.update(values)
        return subprocess.run(['bash', '-c', 'source setup-apt.sh; select_suite'],
                              cwd=ROOT, env=env, capture_output=True, text=True)

    def test_debian_releases(self):
        for suite in ('bookworm', 'trixie'):
            with self.subTest(suite=suite):
                result = self.select(ID='debian', VERSION_CODENAME=suite)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), suite)

    def test_ubuntu_releases(self):
        for suite in ('jammy', 'noble', 'resolute'):
            result = self.select(ID='ubuntu', ID_LIKE='debian', VERSION_CODENAME=suite)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), suite)

    def test_derivative_prefers_base(self):
        result = self.select(ID='linuxmint', ID_LIKE='ubuntu debian',
                             VERSION_CODENAME='xia', UBUNTU_CODENAME='noble')
        self.assertEqual(result.stdout.strip(), 'noble')
        result = self.select(ID='linuxmint', ID_LIKE='debian',
                             VERSION_CODENAME='faye', DEBIAN_CODENAME='bookworm')
        self.assertEqual(result.stdout.strip(), 'bookworm')

    def test_unknown_base_fails_closed(self):
        for values in [dict(ID='arch', VERSION_CODENAME='noble'),
                       dict(ID='kali', ID_LIKE='debian', VERSION_CODENAME='kali-rolling'),
                       dict(ID='debian', VERSION_CODENAME='bullseye')]:
            self.assertNotEqual(self.select(**values).returncode, 0)

    def test_unique_debian_versions(self):
        result = subprocess.check_output(['bash', '-c',
            'source packaging/debian/targets.sh; while read -r t; do '
            'retrocast_package_version 0.1.1 "$t"; done < <(retrocast_targets)'],
            cwd=ROOT, text=True).splitlines()
        self.assertEqual(len(set(result)), 5)
        self.assertIn('0.1.1+noble', result)

    def test_unknown_build_target_rejected(self):
        result = subprocess.run(['bash', '-c',
            'source packaging/debian/targets.sh; retrocast_image unknown'],
            cwd=ROOT, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
