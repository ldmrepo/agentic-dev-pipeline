"""
보안 감사 전문 에이전트
애플리케이션, 인프라, 코드의 보안 취약점을 탐지하고 자동으로 수정하는 AI 에이전트
"""

import asyncio
import subprocess
import json
import yaml
import re
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import aiohttp
import aiofiles
from pathlib import Path
import ast
import base64

class VulnerabilityType(Enum):
    """보안 취약점 유형"""
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    WEAK_AUTHENTICATION = "weak_authentication"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    VULNERABLE_DEPENDENCY = "vulnerable_dependency"
    HARDCODED_SECRET = "hardcoded_secret"
    WEAK_CRYPTOGRAPHY = "weak_cryptography"
    INSUFFICIENT_LOGGING = "insufficient_logging"

@dataclass
class SecurityVulnerability:
    """보안 취약점 정보"""
    vulnerability_type: VulnerabilityType
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: Optional[int]
    description: str
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    evidence: str
    remediation: str
    fix_available: bool = False
    auto_fixable: bool = False

@dataclass
class SecurityFix:
    """보안 수정 사항"""
    vulnerability_id: str
    fix_type: str  # code_change, config_change, dependency_update
    original_code: str
    fixed_code: str
    validation_required: bool = True
    risk_level: str = "low"

class CodeSecurityAnalyzer:
    """코드 보안 분석기"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        
    def _load_vulnerability_patterns(self) -> Dict[str, List[Dict]]:
        """보안 취약점 패턴 로드"""
        return {
            'python': [
                {
                    'type': VulnerabilityType.SQL_INJECTION,
                    'pattern': r'(execute|executemany)\s*\(\s*["\'].*%[s|d].*["\'].*%',
                    'severity': 'critical',
                    'cwe': 'CWE-89',
                    'description': 'SQL 인젝션 취약점: 파라미터화되지 않은 쿼리'
                },
                {
                    'type': VulnerabilityType.COMMAND_INJECTION,
                    'pattern': r'(os\.system|subprocess\.call|subprocess\.run)\s*\([^)]*\+[^)]*\)',
                    'severity': 'critical',
                    'cwe': 'CWE-78',
                    'description': '명령어 인젝션: 사용자 입력이 시스템 명령에 포함됨'
                },
                {
                    'type': VulnerabilityType.HARDCODED_SECRET,
                    'pattern': r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                    'severity': 'high',
                    'cwe': 'CWE-798',
                    'description': '하드코딩된 인증 정보'
                },
                {
                    'type': VulnerabilityType.WEAK_CRYPTOGRAPHY,
                    'pattern': r'(md5|sha1)\s*\(',
                    'severity': 'medium',
                    'cwe': 'CWE-328',
                    'description': '약한 암호화 알고리즘 사용'
                },
                {
                    'type': VulnerabilityType.PATH_TRAVERSAL,
                    'pattern': r'open\s*\([^)]*\+[^)]*\)',
                    'severity': 'high',
                    'cwe': 'CWE-22',
                    'description': '경로 조작 취약점'
                }
            ],
            'javascript': [
                {
                    'type': VulnerabilityType.XSS,
                    'pattern': r'innerHTML\s*=\s*[^;]+(?:request|req|params|query)',
                    'severity': 'high',
                    'cwe': 'CWE-79',
                    'description': 'XSS 취약점: 사용자 입력이 innerHTML에 직접 삽입됨'
                },
                {
                    'type': VulnerabilityType.SQL_INJECTION,
                    'pattern': r'query\s*\(\s*["\'].*\+.*["\']',
                    'severity': 'critical',
                    'cwe': 'CWE-89',
                    'description': 'SQL 인젝션: 문자열 연결로 쿼리 생성'
                },
                {
                    'type': VulnerabilityType.INSECURE_DESERIALIZATION,
                    'pattern': r'eval\s*\(',
                    'severity': 'critical',
                    'cwe': 'CWE-502',
                    'description': '안전하지 않은 역직렬화: eval() 사용'
                }
            ]
        }
    
    async def analyze_code(self, file_path: str) -> List[SecurityVulnerability]:
        """코드 보안 분석"""
        vulnerabilities = []
        
        # 파일 확장자로 언어 판별
        ext = Path(file_path).suffix.lower()
        language = None
        if ext in ['.py']:
            language = 'python'
        elif ext in ['.js', '.ts']:
            language = 'javascript'
        
        if not language or language not in self.vulnerability_patterns:
            return vulnerabilities
        
        # 파일 읽기
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            return vulnerabilities
        
        # 패턴 매칭
        patterns = self.vulnerability_patterns[language]
        
        for pattern_info in patterns:
            pattern = re.compile(pattern_info['pattern'], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    vulnerability = SecurityVulnerability(
                        vulnerability_type=pattern_info['type'],
                        severity=pattern_info['severity'],
                        file_path=file_path,
                        line_number=i,
                        description=pattern_info['description'],
                        cwe_id=pattern_info['cwe'],
                        owasp_category=self._get_owasp_category(pattern_info['type']),
                        evidence=line.strip(),
                        remediation=self._get_remediation(pattern_info['type']),
                        auto_fixable=self._is_auto_fixable(pattern_info['type'])
                    )
                    vulnerabilities.append(vulnerability)
        
        # AST 기반 고급 분석 (Python)
        if language == 'python':
            ast_vulnerabilities = await self._analyze_python_ast(file_path, content)
            vulnerabilities.extend(ast_vulnerabilities)
        
        return vulnerabilities
    
    async def _analyze_python_ast(self, file_path: str, content: str) -> List[SecurityVulnerability]:
        """Python AST 기반 보안 분석"""
        vulnerabilities = []
        
        try:
            tree = ast.parse(content)
            
            class SecurityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.vulnerabilities = []
                
                def visit_Call(self, node):
                    # pickle 사용 검사
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr in ['loads', 'load'] and
                        isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == 'pickle'):
                        
                        self.vulnerabilities.append(SecurityVulnerability(
                            vulnerability_type=VulnerabilityType.INSECURE_DESERIALIZATION,
                            severity='high',
                            file_path=file_path,
                            line_number=node.lineno,
                            description='안전하지 않은 pickle 역직렬화',
                            cwe_id='CWE-502',
                            owasp_category='A8',
                            evidence=f'pickle.{node.func.attr}() 사용',
                            remediation='JSON 또는 다른 안전한 직렬화 형식 사용',
                            auto_fixable=True
                        ))
                    
                    # exec 사용 검사
                    if (isinstance(node.func, ast.Name) and 
                        node.func.id in ['exec', 'eval']):
                        
                        self.vulnerabilities.append(SecurityVulnerability(
                            vulnerability_type=VulnerabilityType.COMMAND_INJECTION,
                            severity='critical',
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f'위험한 {node.func.id}() 사용',
                            cwe_id='CWE-95',
                            owasp_category='A3',
                            evidence=f'{node.func.id}() 호출',
                            remediation='동적 코드 실행 제거 또는 안전한 대안 사용',
                            auto_fixable=False
                        ))
                    
                    self.generic_visit(node)
                
                def visit_Import(self, node):
                    # 위험한 모듈 import 검사
                    dangerous_modules = ['pickle', 'marshal', 'shelve']
                    for alias in node.names:
                        if alias.name in dangerous_modules:
                            self.vulnerabilities.append(SecurityVulnerability(
                                vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                                severity='medium',
                                file_path=file_path,
                                line_number=node.lineno,
                                description=f'잠재적으로 위험한 모듈 import: {alias.name}',
                                cwe_id='CWE-676',
                                owasp_category='A6',
                                evidence=f'import {alias.name}',
                                remediation='안전한 대안 모듈 사용 고려',
                                auto_fixable=False
                            ))
                    
                    self.generic_visit(node)
            
            visitor = SecurityVisitor()
            visitor.visit(tree)
            vulnerabilities.extend(visitor.vulnerabilities)
            
        except SyntaxError:
            print(f"Python 파일 파싱 오류: {file_path}")
        
        return vulnerabilities
    
    def _get_owasp_category(self, vuln_type: VulnerabilityType) -> str:
        """OWASP Top 10 카테고리 매핑"""
        mapping = {
            VulnerabilityType.SQL_INJECTION: "A03:2021",
            VulnerabilityType.XSS: "A03:2021",
            VulnerabilityType.COMMAND_INJECTION: "A03:2021",
            VulnerabilityType.WEAK_AUTHENTICATION: "A07:2021",
            VulnerabilityType.SENSITIVE_DATA_EXPOSURE: "A02:2021",
            VulnerabilityType.SECURITY_MISCONFIGURATION: "A05:2021",
            VulnerabilityType.VULNERABLE_DEPENDENCY: "A06:2021",
            VulnerabilityType.INSUFFICIENT_LOGGING: "A09:2021"
        }
        return mapping.get(vuln_type, "A10:2021")
    
    def _get_remediation(self, vuln_type: VulnerabilityType) -> str:
        """취약점별 수정 방법"""
        remediations = {
            VulnerabilityType.SQL_INJECTION: "파라미터화된 쿼리 또는 ORM 사용",
            VulnerabilityType.XSS: "사용자 입력 이스케이프 및 Content Security Policy 적용",
            VulnerabilityType.COMMAND_INJECTION: "사용자 입력 검증 및 안전한 API 사용",
            VulnerabilityType.PATH_TRAVERSAL: "경로 정규화 및 화이트리스트 검증",
            VulnerabilityType.HARDCODED_SECRET: "환경 변수 또는 비밀 관리 서비스 사용",
            VulnerabilityType.WEAK_CRYPTOGRAPHY: "강력한 암호화 알고리즘 (AES, SHA-256) 사용",
            VulnerabilityType.INSECURE_DESERIALIZATION: "신뢰할 수 있는 데이터만 역직렬화"
        }
        return remediations.get(vuln_type, "보안 모범 사례 적용")
    
    def _is_auto_fixable(self, vuln_type: VulnerabilityType) -> bool:
        """자동 수정 가능 여부"""
        auto_fixable_types = [
            VulnerabilityType.HARDCODED_SECRET,
            VulnerabilityType.WEAK_CRYPTOGRAPHY,
            VulnerabilityType.SQL_INJECTION,  # 간단한 경우만
            VulnerabilityType.INSECURE_DESERIALIZATION
        ]
        return vuln_type in auto_fixable_types

class DependencyScanner:
    """의존성 보안 스캐너"""
    
    async def scan_dependencies(self, project_path: str) -> List[SecurityVulnerability]:
        """프로젝트 의존성 보안 검사"""
        vulnerabilities = []
        
        # package.json (Node.js)
        package_json_path = Path(project_path) / 'package.json'
        if package_json_path.exists():
            npm_vulns = await self._scan_npm_dependencies(project_path)
            vulnerabilities.extend(npm_vulns)
        
        # requirements.txt (Python)
        requirements_path = Path(project_path) / 'requirements.txt'
        if requirements_path.exists():
            pip_vulns = await self._scan_pip_dependencies(project_path)
            vulnerabilities.extend(pip_vulns)
        
        # Dockerfile
        dockerfile_path = Path(project_path) / 'Dockerfile'
        if dockerfile_path.exists():
            docker_vulns = await self._scan_docker_image(dockerfile_path)
            vulnerabilities.extend(docker_vulns)
        
        return vulnerabilities
    
    async def _scan_npm_dependencies(self, project_path: str) -> List[SecurityVulnerability]:
        """NPM 의존성 검사"""
        vulnerabilities = []
        
        try:
            # npm audit 실행
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and result.stdout:
                audit_data = json.loads(result.stdout)
                
                for advisory_id, advisory in audit_data.get('advisories', {}).items():
                    vulnerability = SecurityVulnerability(
                        vulnerability_type=VulnerabilityType.VULNERABLE_DEPENDENCY,
                        severity=self._map_npm_severity(advisory['severity']),
                        file_path='package.json',
                        line_number=None,
                        description=f"{advisory['module_name']}: {advisory['title']}",
                        cwe_id=advisory.get('cwe'),
                        owasp_category="A06:2021",
                        evidence=f"버전 {advisory['vulnerable_versions']}에 취약점 존재",
                        remediation=f"버전 {advisory['patched_versions']}로 업데이트",
                        auto_fixable=True
                    )
                    vulnerabilities.append(vulnerability)
        
        except Exception as e:
            print(f"NPM 의존성 스캔 오류: {e}")
        
        return vulnerabilities
    
    async def _scan_pip_dependencies(self, project_path: str) -> List[SecurityVulnerability]:
        """Python 의존성 검사"""
        vulnerabilities = []
        
        try:
            # pip-audit 실행
            result = subprocess.run(
                ['pip-audit', '--format', 'json', '-r', 'requirements.txt'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                audit_data = json.loads(result.stdout)
                
                for vuln in audit_data:
                    vulnerability = SecurityVulnerability(
                        vulnerability_type=VulnerabilityType.VULNERABLE_DEPENDENCY,
                        severity=self._map_severity_score(vuln.get('severity', 'UNKNOWN')),
                        file_path='requirements.txt',
                        line_number=None,
                        description=f"{vuln['name']}: {vuln['description']}",
                        cwe_id=None,
                        owasp_category="A06:2021",
                        evidence=f"버전 {vuln['version']}에 취약점 존재",
                        remediation=f"버전 {vuln.get('fixed_version', '최신 버전')}로 업데이트",
                        auto_fixable=True
                    )
                    vulnerabilities.append(vulnerability)
        
        except Exception as e:
            print(f"Python 의존성 스캔 오류: {e}")
        
        return vulnerabilities
    
    async def _scan_docker_image(self, dockerfile_path: Path) -> List[SecurityVulnerability]:
        """Docker 이미지 보안 검사"""
        vulnerabilities = []
        
        try:
            # Trivy 실행
            result = subprocess.run(
                ['trivy', 'config', str(dockerfile_path), '--format', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                trivy_data = json.loads(result.stdout)
                
                for result in trivy_data.get('Results', []):
                    for vuln in result.get('Vulnerabilities', []):
                        vulnerability = SecurityVulnerability(
                            vulnerability_type=VulnerabilityType.VULNERABLE_DEPENDENCY,
                            severity=vuln['Severity'].lower(),
                            file_path=str(dockerfile_path),
                            line_number=None,
                            description=f"{vuln['PkgName']}: {vuln['Title']}",
                            cwe_id=vuln.get('CweIDs', [None])[0] if vuln.get('CweIDs') else None,
                            owasp_category="A06:2021",
                            evidence=vuln['Description'][:200],
                            remediation=f"버전 {vuln.get('FixedVersion', '패치 버전')}로 업데이트",
                            auto_fixable=bool(vuln.get('FixedVersion'))
                        )
                        vulnerabilities.append(vulnerability)
        
        except Exception as e:
            print(f"Docker 이미지 스캔 오류: {e}")
        
        return vulnerabilities
    
    def _map_npm_severity(self, npm_severity: str) -> str:
        """NPM 심각도를 표준 심각도로 매핑"""
        mapping = {
            'critical': 'critical',
            'high': 'high',
            'moderate': 'medium',
            'low': 'low'
        }
        return mapping.get(npm_severity.lower(), 'medium')
    
    def _map_severity_score(self, score: str) -> str:
        """CVSS 점수를 심각도로 매핑"""
        if 'CRITICAL' in score or float(score) >= 9.0 if score.replace('.', '').isdigit() else False:
            return 'critical'
        elif 'HIGH' in score or float(score) >= 7.0 if score.replace('.', '').isdigit() else False:
            return 'high'
        elif 'MEDIUM' in score or float(score) >= 4.0 if score.replace('.', '').isdigit() else False:
            return 'medium'
        else:
            return 'low'

class SecurityRemediator:
    """보안 취약점 자동 수정"""
    
    async def generate_fix(self, vulnerability: SecurityVulnerability) -> Optional[SecurityFix]:
        """취약점에 대한 수정 생성"""
        
        if not vulnerability.auto_fixable:
            return None
        
        fix_generators = {
            VulnerabilityType.SQL_INJECTION: self._fix_sql_injection,
            VulnerabilityType.HARDCODED_SECRET: self._fix_hardcoded_secret,
            VulnerabilityType.WEAK_CRYPTOGRAPHY: self._fix_weak_crypto,
            VulnerabilityType.INSECURE_DESERIALIZATION: self._fix_insecure_deserialization
        }
        
        generator = fix_generators.get(vulnerability.vulnerability_type)
        if generator:
            return await generator(vulnerability)
        
        return None
    
    async def _fix_sql_injection(self, vuln: SecurityVulnerability) -> SecurityFix:
        """SQL 인젝션 수정"""
        original = vuln.evidence
        
        # 간단한 문자열 포맷팅을 파라미터화된 쿼리로 변경
        if '%.format(' in original or '%s' in original:
            fixed = re.sub(
                r'(["\'])([^"\']*%[sd][^"\']*)["\']\s*%\s*\((.*?)\)',
                r'(\1\2\1, \3)',
                original
            )
        else:
            # f-string 또는 + 연산자 사용 케이스
            fixed = "# TODO: 파라미터화된 쿼리로 변경 필요\n# " + original
        
        return SecurityFix(
            vulnerability_id=hashlib.md5(str(vuln).encode()).hexdigest(),
            fix_type='code_change',
            original_code=original,
            fixed_code=fixed,
            validation_required=True,
            risk_level='medium'
        )
    
    async def _fix_hardcoded_secret(self, vuln: SecurityVulnerability) -> SecurityFix:
        """하드코딩된 비밀 정보 수정"""
        original = vuln.evidence
        
        # 변수명 추출
        match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', original)
        if match:
            var_name = match.group(1)
            
            # 환경 변수로 대체
            fixed = f"{var_name} = os.environ.get('{var_name.upper()}', '')"
            
            # .env 파일 생성 코드 추가
            env_content = f"\n# .env 파일에 추가:\n# {var_name.upper()}=your_secret_value_here"
            
            return SecurityFix(
                vulnerability_id=hashlib.md5(str(vuln).encode()).hexdigest(),
                fix_type='code_change',
                original_code=original,
                fixed_code=f"import os\n{fixed}{env_content}",
                validation_required=True,
                risk_level='low'
            )
        
        return None
    
    async def _fix_weak_crypto(self, vuln: SecurityVulnerability) -> SecurityFix:
        """약한 암호화 알고리즘 수정"""
        original = vuln.evidence
        
        # MD5/SHA1을 SHA256으로 변경
        fixed = original
        fixed = re.sub(r'\bmd5\b', 'sha256', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'\bsha1\b', 'sha256', fixed, flags=re.IGNORECASE)
        
        # hashlib import 수정
        if 'hashlib' in fixed:
            fixed = fixed.replace('hashlib.md5', 'hashlib.sha256')
            fixed = fixed.replace('hashlib.sha1', 'hashlib.sha256')
        
        return SecurityFix(
            vulnerability_id=hashlib.md5(str(vuln).encode()).hexdigest(),
            fix_type='code_change',
            original_code=original,
            fixed_code=fixed,
            validation_required=False,
            risk_level='low'
        )
    
    async def _fix_insecure_deserialization(self, vuln: SecurityVulnerability) -> SecurityFix:
        """안전하지 않은 역직렬화 수정"""
        original = vuln.evidence
        
        # pickle을 JSON으로 변경
        if 'pickle' in original:
            fixed = original
            fixed = re.sub(r'pickle\.loads?\(', 'json.loads(', fixed)
            fixed = re.sub(r'pickle\.dumps?\(', 'json.dumps(', fixed)
            
            return SecurityFix(
                vulnerability_id=hashlib.md5(str(vuln).encode()).hexdigest(),
                fix_type='code_change',
                original_code=original,
                fixed_code=f"import json\n{fixed}",
                validation_required=True,
                risk_level='medium'
            )
        
        return None

class SecurityAuditAgent:
    """보안 감사 전문 에이전트"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.code_analyzer = CodeSecurityAnalyzer()
        self.dependency_scanner = DependencyScanner()
        self.remediator = SecurityRemediator()
        self.scan_history = []
    
    async def perform_security_audit(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """전체 보안 감사 수행"""
        
        print("🔒 보안 감사를 시작합니다...")
        
        all_vulnerabilities = []
        
        # 1. 코드 보안 분석
        if 'source_files' in project_config:
            print("📝 소스 코드 보안 분석 중...")
            for file_path in project_config['source_files']:
                vulnerabilities = await self.code_analyzer.analyze_code(file_path)
                all_vulnerabilities.extend(vulnerabilities)
        
        # 2. 의존성 보안 검사
        if 'project_path' in project_config:
            print("📦 의존성 보안 검사 중...")
            dep_vulnerabilities = await self.dependency_scanner.scan_dependencies(
                project_config['project_path']
            )
            all_vulnerabilities.extend(dep_vulnerabilities)
        
        # 3. 인프라 보안 검사
        if 'infrastructure' in project_config:
            print("🏗️ 인프라 보안 검사 중...")
            infra_vulnerabilities = await self._scan_infrastructure(
                project_config['infrastructure']
            )
            all_vulnerabilities.extend(infra_vulnerabilities)
        
        # 4. 웹 애플리케이션 보안 테스트 (DAST)
        if 'web_endpoints' in project_config:
            print("🌐 웹 애플리케이션 보안 테스트 중...")
            web_vulnerabilities = await self._perform_dast(
                project_config['web_endpoints']
            )
            all_vulnerabilities.extend(web_vulnerabilities)
        
        # 5. 취약점 분석 및 우선순위 결정
        prioritized_vulnerabilities = self._prioritize_vulnerabilities(all_vulnerabilities)
        
        # 6. 자동 수정 생성
        fixes = []
        if project_config.get('auto_fix', False):
            print("🔧 자동 수정 생성 중...")
            for vuln in prioritized_vulnerabilities:
                if vuln.auto_fixable:
                    fix = await self.remediator.generate_fix(vuln)
                    if fix:
                        fixes.append(fix)
        
        # 7. 컴플라이언스 체크
        compliance_status = self._check_compliance(
            all_vulnerabilities,
            project_config.get('compliance_frameworks', [])
        )
        
        # 8. 보고서 생성
        report = self._generate_security_report(
            prioritized_vulnerabilities,
            fixes,
            compliance_status,
            project_config
        )
        
        print("✅ 보안 감사가 완료되었습니다!")
        
        # 이력 저장
        self.scan_history.append({
            'timestamp': datetime.now(),
            'vulnerabilities_found': len(all_vulnerabilities),
            'critical_count': sum(1 for v in all_vulnerabilities if v.severity == 'critical'),
            'auto_fixes_generated': len(fixes)
        })
        
        return report
    
    async def _scan_infrastructure(self, infra_config: Dict[str, Any]) -> List[SecurityVulnerability]:
        """인프라 보안 검사"""
        vulnerabilities = []
        
        # Kubernetes 보안 검사
        if 'kubernetes' in infra_config:
            k8s_vulns = await self._scan_kubernetes(infra_config['kubernetes'])
            vulnerabilities.extend(k8s_vulns)
        
        # 클라우드 보안 검사
        if 'cloud' in infra_config:
            cloud_vulns = await self._scan_cloud_resources(infra_config['cloud'])
            vulnerabilities.extend(cloud_vulns)
        
        return vulnerabilities
    
    async def _scan_kubernetes(self, k8s_config: Dict[str, Any]) -> List[SecurityVulnerability]:
        """Kubernetes 보안 검사"""
        vulnerabilities = []
        
        # kubesec을 사용한 매니페스트 스캔
        for manifest_file in k8s_config.get('manifests', []):
            try:
                result = subprocess.run(
                    ['kubesec', 'scan', manifest_file],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    scan_results = json.loads(result.stdout)
                    
                    for result in scan_results:
                        if result['score'] < 0:
                            vulnerability = SecurityVulnerability(
                                vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                                severity='high' if result['score'] < -5 else 'medium',
                                file_path=manifest_file,
                                line_number=None,
                                description="Kubernetes 보안 설정 문제",
                                cwe_id='CWE-16',
                                owasp_category='A05:2021',
                                evidence="; ".join(result.get('critical', [])),
                                remediation="; ".join(result.get('advise', [])),
                                auto_fixable=False
                            )
                            vulnerabilities.append(vulnerability)
            
            except Exception as e:
                print(f"Kubernetes 스캔 오류: {e}")
        
        return vulnerabilities
    
    async def _perform_dast(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """동적 애플리케이션 보안 테스트"""
        vulnerabilities = []
        
        # OWASP ZAP API를 사용한 스캔 (예시)
        for endpoint in endpoints:
            # 실제 구현에서는 ZAP API 호출
            # 여기서는 간단한 체크만 수행
            
            # HTTPS 체크
            if endpoint.startswith('http://'):
                vulnerabilities.append(SecurityVulnerability(
                    vulnerability_type=VulnerabilityType.SENSITIVE_DATA_EXPOSURE,
                    severity='medium',
                    file_path='web_configuration',
                    line_number=None,
                    description=f"HTTPS 미사용: {endpoint}",
                    cwe_id='CWE-319',
                    owasp_category='A02:2021',
                    evidence=f"HTTP 프로토콜 사용 중",
                    remediation="HTTPS로 전환 및 HSTS 헤더 설정",
                    auto_fixable=False
                ))
            
            # 보안 헤더 체크
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint) as response:
                        headers = response.headers
                        
                        # 필수 보안 헤더 체크
                        security_headers = {
                            'X-Frame-Options': 'Clickjacking 방지',
                            'X-Content-Type-Options': 'MIME 스니핑 방지',
                            'Content-Security-Policy': 'XSS 및 인젝션 공격 방지',
                            'Strict-Transport-Security': 'HTTPS 강제'
                        }
                        
                        for header, purpose in security_headers.items():
                            if header not in headers:
                                vulnerabilities.append(SecurityVulnerability(
                                    vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                                    severity='low',
                                    file_path='web_server_config',
                                    line_number=None,
                                    description=f"보안 헤더 누락: {header}",
                                    cwe_id='CWE-16',
                                    owasp_category='A05:2021',
                                    evidence=f"{purpose}를 위한 {header} 헤더 없음",
                                    remediation=f"{header} 헤더 추가",
                                    auto_fixable=True
                                ))
            
            except Exception as e:
                print(f"엔드포인트 스캔 오류 {endpoint}: {e}")
        
        return vulnerabilities
    
    def _prioritize_vulnerabilities(self, vulnerabilities: List[SecurityVulnerability]) -> List[SecurityVulnerability]:
        """취약점 우선순위 결정"""
        
        severity_score = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        # CVSS 점수와 악용 가능성을 고려한 정렬
        def vulnerability_score(vuln: SecurityVulnerability) -> float:
            base_score = severity_score.get(vuln.severity, 0)
            
            # 특정 취약점 유형에 가중치 부여
            if vuln.vulnerability_type in [
                VulnerabilityType.SQL_INJECTION,
                VulnerabilityType.COMMAND_INJECTION,
                VulnerabilityType.INSECURE_DESERIALIZATION
            ]:
                base_score *= 1.5
            
            # 자동 수정 가능한 경우 약간 낮은 우선순위
            if vuln.auto_fixable:
                base_score *= 0.9
            
            return base_score
        
        return sorted(vulnerabilities, key=vulnerability_score, reverse=True)
    
    def _check_compliance(self, vulnerabilities: List[SecurityVulnerability], frameworks: List[str]) -> Dict[str, Any]:
        """컴플라이언스 체크"""
        
        compliance_status = {}
        
        for framework in frameworks:
            if framework == 'PCI_DSS':
                compliance_status['PCI_DSS'] = self._check_pci_dss_compliance(vulnerabilities)
            elif framework == 'GDPR':
                compliance_status['GDPR'] = self._check_gdpr_compliance(vulnerabilities)
            elif framework == 'HIPAA':
                compliance_status['HIPAA'] = self._check_hipaa_compliance(vulnerabilities)
        
        return compliance_status
    
    def _check_pci_dss_compliance(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """PCI DSS 컴플라이언스 체크"""
        
        critical_violations = []
        
        # 암호화 관련 체크
        crypto_issues = [v for v in vulnerabilities if v.vulnerability_type == VulnerabilityType.WEAK_CRYPTOGRAPHY]
        if crypto_issues:
            critical_violations.append({
                'requirement': 'PCI DSS 3.4',
                'description': '카드 데이터 암호화 요구사항',
                'violations': len(crypto_issues)
            })
        
        # 접근 제어 체크
        auth_issues = [v for v in vulnerabilities if v.vulnerability_type == VulnerabilityType.WEAK_AUTHENTICATION]
        if auth_issues:
            critical_violations.append({
                'requirement': 'PCI DSS 8.2',
                'description': '강력한 인증 요구사항',
                'violations': len(auth_issues)
            })
        
        return {
            'compliant': len(critical_violations) == 0,
            'violations': critical_violations,
            'risk_level': 'high' if critical_violations else 'low'
        }
    
    def _check_gdpr_compliance(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """GDPR 컴플라이언스 체크"""
        
        privacy_violations = []
        
        # 데이터 보호 체크
        data_exposure = [v for v in vulnerabilities if v.vulnerability_type == VulnerabilityType.SENSITIVE_DATA_EXPOSURE]
        if data_exposure:
            privacy_violations.append({
                'article': 'GDPR Article 32',
                'description': '개인정보 보호를 위한 기술적 조치',
                'violations': len(data_exposure)
            })
        
        # 로깅 체크
        logging_issues = [v for v in vulnerabilities if v.vulnerability_type == VulnerabilityType.INSUFFICIENT_LOGGING]
        if logging_issues:
            privacy_violations.append({
                'article': 'GDPR Article 33',
                'description': '데이터 침해 탐지 및 보고',
                'violations': len(logging_issues)
            })
        
        return {
            'compliant': len(privacy_violations) == 0,
            'violations': privacy_violations,
            'recommendations': ['암호화 강화', '접근 로그 개선', '데이터 최소화']
        }
    
    def _check_hipaa_compliance(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """HIPAA 컴플라이언스 체크"""
        # 구현 생략 (PCI DSS와 유사한 패턴)
        return {'compliant': True, 'violations': []}
    
    def _generate_security_report(
        self,
        vulnerabilities: List[SecurityVulnerability],
        fixes: List[SecurityFix],
        compliance_status: Dict[str, Any],
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """보안 감사 보고서 생성"""
        
        # 취약점 통계
        vuln_stats = {
            'total': len(vulnerabilities),
            'by_severity': {
                'critical': sum(1 for v in vulnerabilities if v.severity == 'critical'),
                'high': sum(1 for v in vulnerabilities if v.severity == 'high'),
                'medium': sum(1 for v in vulnerabilities if v.severity == 'medium'),
                'low': sum(1 for v in vulnerabilities if v.severity == 'low')
            },
            'by_type': {}
        }
        
        # 유형별 집계
        for vuln in vulnerabilities:
            vuln_type = vuln.vulnerability_type.value
            if vuln_type not in vuln_stats['by_type']:
                vuln_stats['by_type'][vuln_type] = 0
            vuln_stats['by_type'][vuln_type] += 1
        
        # 위험 점수 계산
        risk_score = self._calculate_risk_score(vulnerabilities)
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'project_name': project_config.get('project_name', 'Unknown'),
            'executive_summary': {
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'total_vulnerabilities': vuln_stats['total'],
                'critical_issues': vuln_stats['by_severity']['critical'],
                'auto_fixes_available': len(fixes)
            },
            'vulnerability_statistics': vuln_stats,
            'top_vulnerabilities': vulnerabilities[:10],  # 상위 10개
            'compliance_status': compliance_status,
            'remediation_plan': self._create_remediation_plan(vulnerabilities, fixes),
            'security_recommendations': self._generate_recommendations(vulnerabilities),
            'technical_details': {
                'vulnerabilities': [self._vulnerability_to_dict(v) for v in vulnerabilities],
                'fixes': [self._fix_to_dict(f) for f in fixes]
            }
        }
        
        # 보고서 파일 저장
        self._save_report(report)
        
        return report
    
    def _calculate_risk_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """위험 점수 계산 (0-100)"""
        
        if not vulnerabilities:
            return 0
        
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 0.5
        }
        
        total_score = sum(severity_weights.get(v.severity, 0) for v in vulnerabilities)
        
        # 정규화 (최대 100점)
        normalized_score = min(total_score, 100)
        
        return round(normalized_score, 2)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """위험 수준 결정"""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _create_remediation_plan(self, vulnerabilities: List[SecurityVulnerability], fixes: List[SecurityFix]) -> Dict[str, Any]:
        """수정 계획 생성"""
        
        plan = {
            'immediate_actions': [],  # 24시간 이내
            'short_term_actions': [],  # 1주일 이내
            'long_term_actions': []    # 1개월 이내
        }
        
        for vuln in vulnerabilities:
            action = {
                'vulnerability': vuln.description,
                'severity': vuln.severity,
                'remediation': vuln.remediation,
                'auto_fix_available': vuln.auto_fixable
            }
            
            if vuln.severity == 'critical':
                plan['immediate_actions'].append(action)
            elif vuln.severity == 'high':
                plan['short_term_actions'].append(action)
            else:
                plan['long_term_actions'].append(action)
        
        plan['estimated_effort'] = {
            'auto_fixes': f"{len(fixes)} 취약점 자동 수정 가능",
            'manual_fixes': f"{len(vulnerabilities) - len(fixes)} 취약점 수동 수정 필요",
            'total_hours': self._estimate_remediation_hours(vulnerabilities, fixes)
        }
        
        return plan
    
    def _estimate_remediation_hours(self, vulnerabilities: List[SecurityVulnerability], fixes: List[SecurityFix]) -> int:
        """수정 예상 시간 계산"""
        
        hours_per_severity = {
            'critical': 8,
            'high': 4,
            'medium': 2,
            'low': 1
        }
        
        total_hours = 0
        auto_fixed_vulns = {f.vulnerability_id for f in fixes}
        
        for vuln in vulnerabilities:
            vuln_id = hashlib.md5(str(vuln).encode()).hexdigest()
            if vuln_id not in auto_fixed_vulns:
                total_hours += hours_per_severity.get(vuln.severity, 1)
        
        # 자동 수정은 검증 시간만 추가
        total_hours += len(fixes) * 0.5
        
        return int(total_hours)
    
    def _generate_recommendations(self, vulnerabilities: List[SecurityVulnerability]) -> List[str]:
        """보안 권장사항 생성"""
        
        recommendations = []
        
        # 취약점 유형별 권장사항
        vuln_types = set(v.vulnerability_type for v in vulnerabilities)
        
        if VulnerabilityType.SQL_INJECTION in vuln_types:
            recommendations.append("모든 데이터베이스 쿼리에 파라미터화된 쿼리 또는 ORM 사용")
        
        if VulnerabilityType.XSS in vuln_types:
            recommendations.append("사용자 입력 검증 및 출력 인코딩 구현")
        
        if VulnerabilityType.WEAK_AUTHENTICATION in vuln_types:
            recommendations.append("다중 인증(MFA) 구현 및 강력한 패스워드 정책 적용")
        
        if VulnerabilityType.VULNERABLE_DEPENDENCY in vuln_types:
            recommendations.append("정기적인 의존성 업데이트 및 자동화된 취약점 스캔 구현")
        
        # 일반 권장사항
        recommendations.extend([
            "보안 개발 생명주기(SDLC) 프로세스 도입",
            "정기적인 보안 교육 실시",
            "자동화된 보안 테스트를 CI/CD 파이프라인에 통합",
            "침투 테스트 및 보안 감사 정기 실시",
            "보안 사고 대응 계획 수립 및 훈련"
        ])
        
        return recommendations[:10]  # 상위 10개
    
    def _vulnerability_to_dict(self, vuln: SecurityVulnerability) -> Dict[str, Any]:
        """취약점 객체를 딕셔너리로 변환"""
        return {
            'type': vuln.vulnerability_type.value,
            'severity': vuln.severity,
            'file': vuln.file_path,
            'line': vuln.line_number,
            'description': vuln.description,
            'cwe': vuln.cwe_id,
            'owasp': vuln.owasp_category,
            'evidence': vuln.evidence,
            'remediation': vuln.remediation,
            'auto_fixable': vuln.auto_fixable
        }
    
    def _fix_to_dict(self, fix: SecurityFix) -> Dict[str, Any]:
        """수정 객체를 딕셔너리로 변환"""
        return {
            'vulnerability_id': fix.vulnerability_id,
            'type': fix.fix_type,
            'original': fix.original_code,
            'fixed': fix.fixed_code,
            'validation_required': fix.validation_required,
            'risk_level': fix.risk_level
        }
    
    def _save_report(self, report: Dict[str, Any]):
        """보고서 저장"""
        
        # JSON 보고서
        with open('security_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # 마크다운 보고서
        self._generate_markdown_report(report)
        
        # HTML 보고서 (선택적)
        self._generate_html_report(report)
    
    def _generate_markdown_report(self, report: Dict[str, Any]):
        """마크다운 형식 보고서 생성"""
        
        markdown = f"""# 🔒 보안 감사 보고서

**프로젝트**: {report['project_name']}  
**스캔 일시**: {report['scan_date']}

## 📊 요약

- **위험 점수**: {report['executive_summary']['risk_score']}/100
- **위험 수준**: {report['executive_summary']['risk_level']}
- **발견된 취약점**: {report['executive_summary']['total_vulnerabilities']}개
- **심각 취약점**: {report['executive_summary']['critical_issues']}개
- **자동 수정 가능**: {report['executive_summary']['auto_fixes_available']}개

## 🎯 취약점 분포

### 심각도별
- 🔴 Critical: {report['vulnerability_statistics']['by_severity']['critical']}
- 🟠 High: {report['vulnerability_statistics']['by_severity']['high']}
- 🟡 Medium: {report['vulnerability_statistics']['by_severity']['medium']}
- 🟢 Low: {report['vulnerability_statistics']['by_severity']['low']}

### 유형별
"""
        
        for vuln_type, count in report['vulnerability_statistics']['by_type'].items():
            markdown += f"- {vuln_type}: {count}\n"
        
        markdown += f"""
## 🚨 주요 취약점

"""
        
        for i, vuln in enumerate(report['top_vulnerabilities'][:5], 1):
            markdown += f"""
### {i}. {vuln['description']}
- **심각도**: {vuln['severity']}
- **파일**: {vuln['file']}
- **유형**: {vuln['type']}
- **해결 방법**: {vuln['remediation']}
"""
        
        markdown += f"""
## 📋 수정 계획

### 즉시 조치 필요 (24시간 이내)
"""
        for action in report['remediation_plan']['immediate_actions'][:3]:
            markdown += f"- {action['vulnerability']} ({action['severity']})\n"
        
        markdown += f"""
### 단기 조치 (1주일 이내)
"""
        for action in report['remediation_plan']['short_term_actions'][:3]:
            markdown += f"- {action['vulnerability']} ({action['severity']})\n"
        
        markdown += f"""
## 💡 보안 권장사항

"""
        for rec in report['security_recommendations'][:5]:
            markdown += f"- {rec}\n"
        
        with open('security_report.md', 'w') as f:
            f.write(markdown)
    
    def _generate_html_report(self, report: Dict[str, Any]):
        """HTML 보고서 생성"""
        # 구현 생략 (템플릿 엔진 사용)
        pass

# 사용 예시
async def main():
    agent = SecurityAuditAgent('configs/agents/security-audit-agent.yaml')
    
    project_config = {
        'project_name': 'MyWebApp',
        'source_files': [
            'src/api/auth.py',
            'src/api/database.py',
            'src/utils/crypto.py'
        ],
        'project_path': '/path/to/project',
        'web_endpoints': [
            'https://api.example.com',
            'https://admin.example.com'
        ],
        'infrastructure': {
            'kubernetes': {
                'manifests': ['k8s/deployment.yaml', 'k8s/service.yaml']
            }
        },
        'compliance_frameworks': ['PCI_DSS', 'GDPR'],
        'auto_fix': True
    }
    
    report = await agent.perform_security_audit(project_config)
    print(f"\n✅ 보안 감사 완료!")
    print(f"📊 위험 점수: {report['executive_summary']['risk_score']}/100")
    print(f"🚨 심각 취약점: {report['executive_summary']['critical_issues']}개")
    print(f"🔧 자동 수정 가능: {report['executive_summary']['auto_fixes_available']}개")
    print(f"\n📄 상세 보고서: security_report.md")

if __name__ == "__main__":
    asyncio.run(main())