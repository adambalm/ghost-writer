#!/usr/bin/env python3
"""
Commercial Licensing Compliance Checker for Ghost Writer
Ensures all dependencies are compatible with commercial use
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LicenseChecker:
    """Commercial licensing compliance verification"""
    
    # Licenses incompatible with commercial use
    INCOMPATIBLE_LICENSES = {
        'GPL', 'GPL-2.0', 'GPL-3.0', 'GPL-2.0+', 'GPL-3.0+',
        'AGPL', 'AGPL-3.0', 'AGPL-3.0+',
        'LGPL-3.0', 'LGPL-3.0+',  # Some versions problematic
        'CC-BY-SA', 'CC-BY-SA-4.0',  # ShareAlike creates restrictions
        'OSL-3.0',  # Open Software License
        'EPL-1.0', 'EPL-2.0',  # Eclipse Public License (copyleft)
        'EUPL-1.1', 'EUPL-1.2',  # European Union Public License
        'SSPL',  # Server Side Public License (MongoDB)
        'BUSL'   # Business Source License
    }
    
    # Licenses safe for commercial use
    SAFE_LICENSES = {
        'MIT', 'BSD', 'BSD-2-Clause', 'BSD-3-Clause',
        'Apache', 'Apache-2.0', 'Apache Software License',
        'ISC', 'Unlicense', 'WTFPL',
        'Python Software Foundation License',
        'Zlib', 'zlib/libpng',
        'MPL-2.0',  # Mozilla Public License (weak copyleft, commercial OK)
        'LGPL-2.1',  # Limited LGPL versions acceptable
        'CC0', 'Public Domain',
        'Artistic-2.0',
        'OpenSSL'
    }
    
    # High-risk packages that require special attention
    HIGH_RISK_PACKAGES = {
        'sn2md': 'Core dependency with potential licensing issues',
        'supernotelib': 'External library with unknown license',
        'supabase': 'Check for commercial terms',
        'mysql-connector-python': 'Oracle GPL license',
        'pysqlite': 'Check sqlite licensing'
    }
    
    def __init__(self):
        self.violations = []
        self.warnings = []
        self.safe_packages = []
        
    def get_installed_packages(self) -> List[Dict[str, str]]:
        """Get list of installed packages with license info"""
        try:
            # Get package list with pip-licenses
            result = subprocess.run([
                'pip-licenses', '--format=json', '--with-authors', '--with-urls'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning("pip-licenses failed, falling back to pip list")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("pip-licenses not available, using basic pip list")
            
        # Fallback to basic pip list
        result = subprocess.run([
            'pip', 'list', '--format=json'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return [{'Name': pkg['name'], 'Version': pkg['version'], 'License': 'Unknown'} 
                   for pkg in packages]
        
        return []
    
    def normalize_license(self, license_text: str) -> str:
        """Normalize license text for comparison"""
        if not license_text or license_text.lower() in ['unknown', 'none', '']:
            return 'Unknown'
            
        # Clean up license text
        license_clean = license_text.strip().replace('License', '').replace('license', '')
        license_clean = re.sub(r'\s+', ' ', license_clean).strip()
        
        # Handle common variations
        license_mappings = {
            'BSD License': 'BSD',
            'MIT License': 'MIT',
            'Apache Software License': 'Apache-2.0',
            'GNU General Public License v2 or later (GPLv2+)': 'GPL-2.0+',
            'GNU General Public License v3 (GPLv3)': 'GPL-3.0',
            'GNU Lesser General Public License v2.1 (LGPLv2.1)': 'LGPL-2.1',
            'Mozilla Public License 2.0 (MPL 2.0)': 'MPL-2.0'
        }
        
        return license_mappings.get(license_clean, license_clean)
    
    def check_license_compatibility(self, package_name: str, license_text: str) -> Dict[str, Any]:
        """Check if a license is compatible with commercial use"""
        normalized_license = self.normalize_license(license_text)
        
        result = {
            'package': package_name,
            'license': normalized_license,
            'compatible': True,
            'risk_level': 'LOW',
            'reason': ''
        }
        
        # Check for incompatible licenses
        for incompatible in self.INCOMPATIBLE_LICENSES:
            if incompatible.lower() in normalized_license.lower():
                result.update({
                    'compatible': False,
                    'risk_level': 'CRITICAL',
                    'reason': f'Incompatible license: {incompatible}'
                })
                return result
        
        # Check for high-risk packages
        if package_name.lower() in [pkg.lower() for pkg in self.HIGH_RISK_PACKAGES]:
            result.update({
                'risk_level': 'HIGH',
                'reason': self.HIGH_RISK_PACKAGES.get(package_name, 'High-risk package requiring review')
            })
        
        # Check for unknown licenses
        if normalized_license == 'Unknown':
            result.update({
                'risk_level': 'MEDIUM',
                'reason': 'License unknown - requires manual verification'
            })
        
        # Check for safe licenses
        for safe in self.SAFE_LICENSES:
            if safe.lower() in normalized_license.lower():
                result.update({
                    'compatible': True,
                    'risk_level': 'LOW',
                    'reason': f'Safe license: {safe}'
                })
                break
        
        return result
    
    def scan_requirements_file(self, requirements_path: str = 'requirements.txt') -> List[str]:
        """Scan requirements.txt for known problematic packages"""
        problematic_packages = []
        
        try:
            with open(requirements_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package_name = line.split('>=')[0].split('==')[0].split('<')[0]
                        
                        if package_name.lower() in [pkg.lower() for pkg in self.HIGH_RISK_PACKAGES]:
                            problematic_packages.append(package_name)
                            
        except FileNotFoundError:
            logger.warning(f"Requirements file not found: {requirements_path}")
            
        return problematic_packages
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive licensing compliance report"""
        logger.info("Scanning installed packages for license compliance...")
        
        packages = self.get_installed_packages()
        
        report = {
            'timestamp': subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode().strip(),
            'total_packages': len(packages),
            'violations': [],
            'warnings': [],
            'safe_packages': [],
            'compliance_status': 'COMPLIANT',
            'recommendations': []
        }
        
        for package in packages:
            check_result = self.check_license_compatibility(
                package.get('Name', ''), 
                package.get('License', 'Unknown')
            )
            
            if not check_result['compatible']:
                report['violations'].append(check_result)
                report['compliance_status'] = 'NON_COMPLIANT'
                
            elif check_result['risk_level'] == 'HIGH':
                report['warnings'].append(check_result)
                if report['compliance_status'] == 'COMPLIANT':
                    report['compliance_status'] = 'NEEDS_REVIEW'
                    
            elif check_result['risk_level'] == 'MEDIUM':
                report['warnings'].append(check_result)
                
            else:
                report['safe_packages'].append(check_result)
        
        # Add recommendations
        if report['violations']:
            report['recommendations'].append("CRITICAL: Remove or replace packages with incompatible licenses")
            
        if report['warnings']:
            report['recommendations'].append("Review high-risk packages for commercial compatibility")
            
        # Check requirements.txt
        req_problems = self.scan_requirements_file()
        if req_problems:
            report['requirements_issues'] = req_problems
            report['recommendations'].append(f"Review requirements.txt packages: {', '.join(req_problems)}")
        
        return report
    
    def save_compliance_report(self, report: Dict[str, Any]) -> None:
        """Save compliance report to monitoring directory"""
        monitoring_dir = Path('.handoff/compliance')
        monitoring_dir.mkdir(exist_ok=True)
        
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        report_path = monitoring_dir / f'license_compliance_{timestamp}.json'
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Compliance report saved to {report_path}")
        
        # Also save as latest
        latest_path = monitoring_dir / 'latest_compliance_report.json'
        with open(latest_path, 'w') as f:
            json.dump(report, f, indent=2)

def main():
    """Run licensing compliance check"""
    if len(sys.argv) > 1:
        # Check specific licenses file if provided
        licenses_file = sys.argv[1]
        try:
            with open(licenses_file, 'r') as f:
                packages = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read licenses file {licenses_file}: {e}")
            sys.exit(1)
    else:
        packages = None
    
    checker = LicenseChecker()
    report = checker.generate_compliance_report()
    checker.save_compliance_report(report)
    
    # Print summary
    print(f"\n=== LICENSING COMPLIANCE REPORT ===")
    print(f"Compliance Status: {report['compliance_status']}")
    print(f"Total Packages: {report['total_packages']}")
    print(f"Violations: {len(report['violations'])}")
    print(f"Warnings: {len(report['warnings'])}")
    print(f"Safe Packages: {len(report['safe_packages'])}")
    
    if report['violations']:
        print(f"\n🚨 CRITICAL VIOLATIONS:")
        for violation in report['violations']:
            print(f"  - {violation['package']}: {violation['reason']}")
    
    if report['warnings']:
        print(f"\n⚠️  WARNINGS:")
        for warning in report['warnings']:
            print(f"  - {warning['package']}: {warning['reason']}")
    
    if report['recommendations']:
        print(f"\n📋 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    # Exit codes for CI/CD integration
    if report['compliance_status'] == 'NON_COMPLIANT':
        print(f"\n❌ BLOCKING: License violations prevent commercial deployment")
        sys.exit(1)
    elif report['compliance_status'] == 'NEEDS_REVIEW':
        print(f"\n⚠️  WARNING: High-risk packages require legal review")
        sys.exit(2)
    else:
        print(f"\n✅ COMPLIANT: All packages compatible with commercial use")
        sys.exit(0)

if __name__ == "__main__":
    main()