#!/usr/bin/env python3
"""
Enterprise Risk Monitoring for Ghost Writer Production Deployment
Monitors critical risk indicators and triggers automated responses
"""

import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskMonitor:
    """Enterprise risk monitoring system"""
    
    def __init__(self, config_path: str = "config/risk_config.yaml"):
        self.config_path = Path(config_path)
        self.risk_thresholds = {
            'content_extraction_rate': 80.0,  # Minimum % of sn2md baseline
            'test_coverage': 65.0,            # Minimum test coverage %
            'daily_cost_limit': 50.0,         # Maximum daily API costs
            'error_rate': 5.0,                # Maximum error rate %
            'processing_time': 30.0,          # Maximum seconds per page
            'licensing_violations': 0          # Zero tolerance for GPL/AGPL
        }
        
    def check_content_extraction_risk(self) -> Dict[str, Any]:
        """Monitor content extraction quality vs baseline"""
        try:
            # Run production readiness assessment
            result = subprocess.run([
                'python', 'production_readiness_assessment.py'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                baseline_gap = data['analysis']['remaining_gap']
                extraction_rate = (1 - baseline_gap) * 100
                
                risk_level = "LOW"
                if extraction_rate < self.risk_thresholds['content_extraction_rate']:
                    risk_level = "CRITICAL"
                elif extraction_rate < 90.0:
                    risk_level = "HIGH"
                    
                return {
                    'metric': 'content_extraction_rate',
                    'value': extraction_rate,
                    'threshold': self.risk_thresholds['content_extraction_rate'],
                    'risk_level': risk_level,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Content extraction check failed: {e}")
            
        return {'metric': 'content_extraction_rate', 'risk_level': 'UNKNOWN', 'error': str(e)}
    
    def check_test_coverage_risk(self) -> Dict[str, Any]:
        """Monitor test coverage compliance"""
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', 'tests/', '--cov=src', 
                '--cov-report=json:coverage.json', '-q'
            ], capture_output=True, text=True, timeout=300)
            
            coverage_file = Path('coverage.json')
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    
                coverage_pct = coverage_data['totals']['percent_covered']
                
                risk_level = "LOW"
                if coverage_pct < self.risk_thresholds['test_coverage']:
                    risk_level = "HIGH"
                elif coverage_pct < 70.0:
                    risk_level = "MEDIUM"
                    
                return {
                    'metric': 'test_coverage',
                    'value': coverage_pct,
                    'threshold': self.risk_thresholds['test_coverage'],
                    'risk_level': risk_level,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Test coverage check failed: {e}")
            
        return {'metric': 'test_coverage', 'risk_level': 'UNKNOWN', 'error': str(e)}
    
    def check_licensing_compliance(self) -> Dict[str, Any]:
        """Monitor for GPL/AGPL licensing violations"""
        try:
            result = subprocess.run([
                'pip', 'list', '--format=json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                violations = []
                
                # Check for known problematic licenses
                risk_packages = ['sn2md', 'supernotelib']
                for pkg in packages:
                    if pkg['name'].lower() in risk_packages:
                        violations.append(pkg)
                
                risk_level = "CRITICAL" if violations else "LOW"
                
                return {
                    'metric': 'licensing_violations',
                    'value': len(violations),
                    'threshold': self.risk_thresholds['licensing_violations'],
                    'risk_level': risk_level,
                    'violations': violations,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"License check failed: {e}")
            
        return {'metric': 'licensing_violations', 'risk_level': 'UNKNOWN', 'error': str(e)}
    
    def check_cost_compliance(self) -> Dict[str, Any]:
        """Monitor daily API cost compliance"""
        try:
            # Check cost tracking database
            cost_file = Path('data/database/daily_costs.json')
            if cost_file.exists():
                with open(cost_file) as f:
                    cost_data = json.load(f)
                    
                today = datetime.now().strftime('%Y-%m-%d')
                daily_cost = cost_data.get(today, 0.0)
                
                risk_level = "LOW"
                if daily_cost > self.risk_thresholds['daily_cost_limit']:
                    risk_level = "HIGH"
                elif daily_cost > self.risk_thresholds['daily_cost_limit'] * 0.8:
                    risk_level = "MEDIUM"
                    
                return {
                    'metric': 'daily_cost',
                    'value': daily_cost,
                    'threshold': self.risk_thresholds['daily_cost_limit'],
                    'risk_level': risk_level,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Cost check failed: {e}")
            
        return {'metric': 'daily_cost', 'risk_level': 'UNKNOWN', 'error': str(e)}
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'risks': [],
            'overall_risk_level': 'LOW',
            'recommendations': []
        }
        
        # Run all risk checks
        checks = [
            self.check_content_extraction_risk(),
            self.check_test_coverage_risk(),
            self.check_licensing_compliance(),
            self.check_cost_compliance()
        ]
        
        critical_risks = 0
        high_risks = 0
        
        for check in checks:
            report['risks'].append(check)
            
            if check.get('risk_level') == 'CRITICAL':
                critical_risks += 1
            elif check.get('risk_level') == 'HIGH':
                high_risks += 1
        
        # Determine overall risk level
        if critical_risks > 0:
            report['overall_risk_level'] = 'CRITICAL'
            report['recommendations'].append("IMMEDIATE ACTION REQUIRED: Critical risks detected")
        elif high_risks > 0:
            report['overall_risk_level'] = 'HIGH'
            report['recommendations'].append("High risks require attention within 24 hours")
        elif high_risks + critical_risks == 0:
            report['overall_risk_level'] = 'LOW'
            report['recommendations'].append("System within acceptable risk parameters")
        
        # Add specific recommendations
        for risk in report['risks']:
            if risk.get('risk_level') == 'CRITICAL':
                if risk['metric'] == 'content_extraction_rate':
                    report['recommendations'].append("Deploy hybrid sn2md approach immediately")
                elif risk['metric'] == 'licensing_violations':
                    report['recommendations'].append("Remove GPL dependencies before production")
                    
        return report
    
    def save_risk_report(self, report: Dict[str, Any]) -> None:
        """Save risk report to monitoring directory"""
        monitoring_dir = Path('.handoff/monitoring')
        monitoring_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = monitoring_dir / f'risk_report_{timestamp}.json'
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Risk report saved to {report_path}")
        
        # Also save as latest
        latest_path = monitoring_dir / 'latest_risk_report.json'
        with open(latest_path, 'w') as f:
            json.dump(report, f, indent=2)

def main():
    """Run risk monitoring assessment"""
    monitor = RiskMonitor()
    report = monitor.generate_risk_report()
    monitor.save_risk_report(report)
    
    # Print summary
    print(f"Risk Assessment Complete - Overall Risk: {report['overall_risk_level']}")
    print(f"Critical Risks: {sum(1 for r in report['risks'] if r.get('risk_level') == 'CRITICAL')}")
    print(f"High Risks: {sum(1 for r in report['risks'] if r.get('risk_level') == 'HIGH')}")
    
    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"- {rec}")
    
    # Exit with error code for CI/CD integration
    if report['overall_risk_level'] == 'CRITICAL':
        exit(1)
    elif report['overall_risk_level'] == 'HIGH':
        exit(2)
    else:
        exit(0)

if __name__ == "__main__":
    main()