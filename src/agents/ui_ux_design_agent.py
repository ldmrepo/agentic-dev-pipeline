"""
UI/UX 디자인 에이전트
사용자 인터페이스와 경험을 분석하고 개선하는 전문 AI 에이전트
"""

import asyncio
import json
import yaml
import re
import colorsys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import subprocess
from pathlib import Path
import aiohttp
import aiofiles
from PIL import Image
import numpy as np
from collections import Counter

class DesignIssueType(Enum):
    """디자인 이슈 유형"""
    ACCESSIBILITY = "accessibility"
    COLOR_CONTRAST = "color_contrast"
    TYPOGRAPHY = "typography"
    LAYOUT = "layout"
    RESPONSIVE = "responsive"
    CONSISTENCY = "consistency"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    VISUAL_HIERARCHY = "visual_hierarchy"
    INTERACTION = "interaction"

@dataclass
class DesignIssue:
    """디자인 이슈 정보"""
    issue_type: DesignIssueType
    severity: str  # critical, high, medium, low
    element: str
    description: str
    current_value: Any
    recommended_value: Any
    wcag_criterion: Optional[str] = None
    impact: Optional[str] = None
    auto_fixable: bool = False

@dataclass
class ColorScheme:
    """색상 스킴"""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    error: str
    warning: str
    success: str
    info: str
    
    def to_css_variables(self) -> str:
        """CSS 변수로 변환"""
        return f"""
:root {{
    --color-primary: {self.primary};
    --color-secondary: {self.secondary};
    --color-accent: {self.accent};
    --color-background: {self.background};
    --color-text: {self.text};
    --color-error: {self.error};
    --color-warning: {self.warning};
    --color-success: {self.success};
    --color-info: {self.info};
}}
"""

@dataclass
class TypographySystem:
    """타이포그래피 시스템"""
    font_family_heading: str
    font_family_body: str
    font_size_base: str
    line_height_base: float
    scale_ratio: float
    
    def generate_scale(self) -> Dict[str, str]:
        """타이포그래피 스케일 생성"""
        base_size = float(self.font_size_base.replace('px', ''))
        scale = {
            'xs': f"{base_size / (self.scale_ratio ** 2):.2f}px",
            'sm': f"{base_size / self.scale_ratio:.2f}px",
            'base': self.font_size_base,
            'lg': f"{base_size * self.scale_ratio:.2f}px",
            'xl': f"{base_size * (self.scale_ratio ** 2):.2f}px",
            '2xl': f"{base_size * (self.scale_ratio ** 3):.2f}px",
            '3xl': f"{base_size * (self.scale_ratio ** 4):.2f}px"
        }
        return scale

class AccessibilityAnalyzer:
    """접근성 분석기"""
    
    def __init__(self):
        self.wcag_criteria = self._load_wcag_criteria()
    
    def _load_wcag_criteria(self) -> Dict[str, Any]:
        """WCAG 기준 로드"""
        return {
            'color_contrast': {
                'normal_text': {'AA': 4.5, 'AAA': 7.0},
                'large_text': {'AA': 3.0, 'AAA': 4.5}
            },
            'touch_target': {
                'minimum_size': 44  # pixels
            },
            'focus_indicator': {
                'minimum_contrast': 3.0
            }
        }
    
    async def analyze_html(self, html_content: str) -> List[DesignIssue]:
        """HTML 접근성 분석"""
        issues = []
        
        # 이미지 alt 텍스트 검사
        img_pattern = re.compile(r'<img[^>]*>', re.IGNORECASE)
        for img_tag in img_pattern.findall(html_content):
            if 'alt=' not in img_tag:
                issues.append(DesignIssue(
                    issue_type=DesignIssueType.ACCESSIBILITY,
                    severity='high',
                    element='img',
                    description='이미지에 대체 텍스트 누락',
                    current_value='alt 속성 없음',
                    recommended_value='의미있는 대체 텍스트 추가',
                    wcag_criterion='1.1.1',
                    impact='스크린 리더 사용자가 이미지 내용을 이해할 수 없음',
                    auto_fixable=False
                ))
        
        # 폼 레이블 검사
        input_pattern = re.compile(r'<input[^>]*type=["\'](?!hidden|submit|button)[^"\']*["\'][^>]*>', re.IGNORECASE)
        label_pattern = re.compile(r'<label[^>]*for=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
        
        inputs = input_pattern.findall(html_content)
        labels = label_pattern.findall(html_content)
        
        for input_tag in inputs:
            id_match = re.search(r'id=["\']([^"\']+)["\']', input_tag)
            if id_match:
                input_id = id_match.group(1)
                if input_id not in labels:
                    issues.append(DesignIssue(
                        issue_type=DesignIssueType.ACCESSIBILITY,
                        severity='high',
                        element=f'input#{input_id}',
                        description='폼 입력 필드에 레이블 누락',
                        current_value='연결된 label 없음',
                        recommended_value='<label> 요소 추가',
                        wcag_criterion='3.3.2',
                        impact='스크린 리더 사용자가 입력 필드의 목적을 알 수 없음',
                        auto_fixable=True
                    ))
        
        # 제목 계층 구조 검사
        heading_pattern = re.compile(r'<h(\d)[^>]*>.*?</h\1>', re.IGNORECASE | re.DOTALL)
        headings = [(int(match.group(1)), match.group(0)) for match in heading_pattern.finditer(html_content)]
        
        prev_level = 0
        for level, heading in headings:
            if prev_level > 0 and level - prev_level > 1:
                issues.append(DesignIssue(
                    issue_type=DesignIssueType.ACCESSIBILITY,
                    severity='medium',
                    element=f'h{level}',
                    description='제목 레벨 건너뛰기',
                    current_value=f'h{prev_level} → h{level}',
                    recommended_value='순차적인 제목 레벨 사용',
                    wcag_criterion='1.3.1',
                    impact='문서 구조 이해 어려움',
                    auto_fixable=False
                ))
            prev_level = level
        
        return issues
    
    def check_color_contrast(self, foreground: str, background: str, font_size: float = 16, is_bold: bool = False) -> Dict[str, Any]:
        """색상 대비 검사"""
        
        # 색상을 RGB로 변환
        fg_rgb = self._hex_to_rgb(foreground)
        bg_rgb = self._hex_to_rgb(background)
        
        # 대비율 계산
        contrast_ratio = self._calculate_contrast_ratio(fg_rgb, bg_rgb)
        
        # 큰 텍스트 여부 판단 (18pt 이상 또는 14pt 이상 볼드)
        is_large = font_size >= 18 or (font_size >= 14 and is_bold)
        
        # WCAG 기준 확인
        criteria = self.wcag_criteria['color_contrast']['large_text' if is_large else 'normal_text']
        
        result = {
            'contrast_ratio': round(contrast_ratio, 2),
            'passes_aa': contrast_ratio >= criteria['AA'],
            'passes_aaa': contrast_ratio >= criteria['AAA'],
            'required_aa': criteria['AA'],
            'required_aaa': criteria['AAA'],
            'is_large_text': is_large
        }
        
        return result
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """HEX 색상을 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """WCAG 대비율 계산"""
        
        def relative_luminance(rgb: Tuple[int, int, int]) -> float:
            """상대 휘도 계산"""
            r, g, b = [x / 255.0 for x in rgb]
            
            # sRGB to linear RGB
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        
        # 대비율 계산 (밝은 색이 분자)
        if l1 > l2:
            return (l1 + 0.05) / (l2 + 0.05)
        else:
            return (l2 + 0.05) / (l1 + 0.05)

class ColorSchemeGenerator:
    """색상 스킴 생성기"""
    
    def generate_scheme(self, base_color: str, scheme_type: str = 'complementary') -> ColorScheme:
        """색상 스킴 생성"""
        
        base_rgb = self._hex_to_rgb(base_color)
        base_hsv = colorsys.rgb_to_hsv(*[x/255.0 for x in base_rgb])
        
        if scheme_type == 'monochromatic':
            return self._generate_monochromatic(base_hsv)
        elif scheme_type == 'analogous':
            return self._generate_analogous(base_hsv)
        elif scheme_type == 'complementary':
            return self._generate_complementary(base_hsv)
        elif scheme_type == 'triadic':
            return self._generate_triadic(base_hsv)
        else:
            return self._generate_complementary(base_hsv)
    
    def _generate_monochromatic(self, base_hsv: Tuple[float, float, float]) -> ColorScheme:
        """단색 스킴 생성"""
        h, s, v = base_hsv
        
        return ColorScheme(
            primary=self._hsv_to_hex(h, s, v),
            secondary=self._hsv_to_hex(h, s * 0.5, v),
            accent=self._hsv_to_hex(h, s, v * 0.8),
            background='#FFFFFF',
            text='#1A1A1A',
            error='#DC2626',
            warning='#F59E0B',
            success='#10B981',
            info='#3B82F6'
        )
    
    def _generate_complementary(self, base_hsv: Tuple[float, float, float]) -> ColorScheme:
        """보색 스킴 생성"""
        h, s, v = base_hsv
        
        # 보색 계산
        complement_h = (h + 0.5) % 1.0
        
        return ColorScheme(
            primary=self._hsv_to_hex(h, s, v),
            secondary=self._hsv_to_hex(complement_h, s * 0.8, v * 0.9),
            accent=self._hsv_to_hex(h, s * 1.2, v * 0.8),
            background='#FAFAFA',
            text='#1F2937',
            error='#EF4444',
            warning='#F59E0B',
            success='#10B981',
            info='#3B82F6'
        )
    
    def _generate_analogous(self, base_hsv: Tuple[float, float, float]) -> ColorScheme:
        """유사색 스킴 생성"""
        h, s, v = base_hsv
        
        # 30도씩 이동한 유사색
        analog1_h = (h + 30/360) % 1.0
        analog2_h = (h - 30/360) % 1.0
        
        return ColorScheme(
            primary=self._hsv_to_hex(h, s, v),
            secondary=self._hsv_to_hex(analog1_h, s * 0.9, v * 0.95),
            accent=self._hsv_to_hex(analog2_h, s * 1.1, v * 0.85),
            background='#FFFFFF',
            text='#111827',
            error='#DC2626',
            warning='#F59E0B',
            success='#059669',
            info='#2563EB'
        )
    
    def _generate_triadic(self, base_hsv: Tuple[float, float, float]) -> ColorScheme:
        """삼색 조화 스킴 생성"""
        h, s, v = base_hsv
        
        # 120도씩 이동한 삼색
        triadic1_h = (h + 120/360) % 1.0
        triadic2_h = (h + 240/360) % 1.0
        
        return ColorScheme(
            primary=self._hsv_to_hex(h, s, v),
            secondary=self._hsv_to_hex(triadic1_h, s * 0.8, v * 0.9),
            accent=self._hsv_to_hex(triadic2_h, s * 0.7, v * 0.95),
            background='#FAFAFA',
            text='#1A1A1A',
            error='#E11D48',
            warning='#F97316',
            success='#10B981',
            info='#6366F1'
        )
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """HEX를 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _hsv_to_hex(self, h: float, s: float, v: float) -> str:
        """HSV를 HEX로 변환"""
        # 범위 제한
        h = max(0, min(1, h))
        s = max(0, min(1, s))
        v = max(0, min(1, v))
        
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )

class ResponsiveAnalyzer:
    """반응형 디자인 분석기"""
    
    def __init__(self):
        self.breakpoints = {
            'mobile': 375,
            'tablet': 768,
            'desktop': 1024,
            'wide': 1440
        }
    
    async def analyze_css(self, css_content: str) -> List[DesignIssue]:
        """CSS 반응형 분석"""
        issues = []
        
        # 미디어 쿼리 찾기
        media_queries = re.findall(r'@media[^{]+{[^}]+}', css_content, re.DOTALL)
        
        # 브레이크포인트 분석
        found_breakpoints = set()
        for query in media_queries:
            widths = re.findall(r'(?:min-width|max-width):\s*(\d+)px', query)
            found_breakpoints.update(int(w) for w in widths)
        
        # 누락된 주요 브레이크포인트 검사
        for device, width in self.breakpoints.items():
            if not any(abs(bp - width) < 50 for bp in found_breakpoints):
                issues.append(DesignIssue(
                    issue_type=DesignIssueType.RESPONSIVE,
                    severity='medium',
                    element='media-queries',
                    description=f'{device} 디바이스용 미디어 쿼리 누락',
                    current_value='없음',
                    recommended_value=f'@media (min-width: {width}px)',
                    impact='특정 디바이스에서 레이아웃 문제 발생 가능',
                    auto_fixable=True
                ))
        
        # 고정 너비 요소 검사
        fixed_widths = re.findall(r'width:\s*(\d+)px', css_content)
        for width in fixed_widths:
            if int(width) > 320:  # 최소 모바일 너비
                issues.append(DesignIssue(
                    issue_type=DesignIssueType.RESPONSIVE,
                    severity='high',
                    element='fixed-width',
                    description=f'고정 너비 {width}px 사용',
                    current_value=f'{width}px',
                    recommended_value='상대적 단위 (%, vw, rem) 사용',
                    impact='작은 화면에서 가로 스크롤 발생',
                    auto_fixable=True
                ))
        
        # 뷰포트 메타 태그 확인 (HTML에서 확인 필요)
        if '<meta name="viewport"' not in css_content:
            # CSS에서는 확인 불가, HTML 분석 시 처리
            pass
        
        return issues
    
    def generate_responsive_grid(self) -> str:
        """반응형 그리드 시스템 생성"""
        
        grid_css = """
/* Responsive Grid System */
.container {
    width: 100%;
    padding-right: 1rem;
    padding-left: 1rem;
    margin-right: auto;
    margin-left: auto;
}

@media (min-width: 576px) {
    .container { max-width: 540px; }
}

@media (min-width: 768px) {
    .container { max-width: 720px; }
}

@media (min-width: 992px) {
    .container { max-width: 960px; }
}

@media (min-width: 1200px) {
    .container { max-width: 1140px; }
}

@media (min-width: 1400px) {
    .container { max-width: 1320px; }
}

.row {
    display: flex;
    flex-wrap: wrap;
    margin-right: -0.75rem;
    margin-left: -0.75rem;
}

.col {
    flex: 1 0 0%;
    padding-right: 0.75rem;
    padding-left: 0.75rem;
}

/* Column sizes */
"""
        
        # 12 컬럼 그리드 생성
        for i in range(1, 13):
            width = (i / 12) * 100
            grid_css += f"""
.col-{i} {{
    flex: 0 0 auto;
    width: {width:.6f}%;
}}
"""
        
        # 반응형 컬럼
        breakpoints = ['sm', 'md', 'lg', 'xl']
        breakpoint_widths = ['576px', '768px', '992px', '1200px']
        
        for bp, width in zip(breakpoints, breakpoint_widths):
            grid_css += f"\n@media (min-width: {width}) {{\n"
            for i in range(1, 13):
                col_width = (i / 12) * 100
                grid_css += f"""    .col-{bp}-{i} {{
        flex: 0 0 auto;
        width: {col_width:.6f}%;
    }}
"""
            grid_css += "}\n"
        
        return grid_css

class DesignSystemGenerator:
    """디자인 시스템 생성기"""
    
    def __init__(self):
        self.color_generator = ColorSchemeGenerator()
        
    def generate_design_system(self, brand_color: str, font_preferences: Dict[str, str] = None) -> Dict[str, Any]:
        """완전한 디자인 시스템 생성"""
        
        # 색상 시스템
        color_scheme = self.color_generator.generate_scheme(brand_color, 'complementary')
        
        # 타이포그래피 시스템
        typography = self._generate_typography_system(font_preferences)
        
        # 스페이싱 시스템
        spacing = self._generate_spacing_system()
        
        # 컴포넌트 스타일
        components = self._generate_component_styles(color_scheme, typography)
        
        return {
            'colors': color_scheme,
            'typography': typography,
            'spacing': spacing,
            'components': components,
            'css': self._generate_css(color_scheme, typography, spacing, components)
        }
    
    def _generate_typography_system(self, preferences: Dict[str, str] = None) -> TypographySystem:
        """타이포그래피 시스템 생성"""
        
        default_preferences = {
            'heading_font': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'body_font': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'base_size': '16px',
            'line_height': 1.5,
            'scale_ratio': 1.25
        }
        
        if preferences:
            default_preferences.update(preferences)
        
        return TypographySystem(
            font_family_heading=default_preferences['heading_font'],
            font_family_body=default_preferences['body_font'],
            font_size_base=default_preferences['base_size'],
            line_height_base=default_preferences['line_height'],
            scale_ratio=default_preferences['scale_ratio']
        )
    
    def _generate_spacing_system(self) -> Dict[str, str]:
        """스페이싱 시스템 생성"""
        
        base = 4  # 4px 기반
        return {
            'xs': f'{base}px',
            'sm': f'{base * 2}px',
            'md': f'{base * 4}px',
            'lg': f'{base * 6}px',
            'xl': f'{base * 8}px',
            '2xl': f'{base * 12}px',
            '3xl': f'{base * 16}px',
            '4xl': f'{base * 24}px'
        }
    
    def _generate_component_styles(self, colors: ColorScheme, typography: TypographySystem) -> Dict[str, str]:
        """컴포넌트 스타일 생성"""
        
        return {
            'button': f"""
.btn {{
    display: inline-block;
    padding: 0.5rem 1rem;
    font-family: {typography.font_family_body};
    font-size: {typography.font_size_base};
    font-weight: 500;
    line-height: {typography.line_height_base};
    text-align: center;
    text-decoration: none;
    vertical-align: middle;
    cursor: pointer;
    user-select: none;
    border: 1px solid transparent;
    border-radius: 0.375rem;
    transition: all 0.15s ease-in-out;
}}

.btn-primary {{
    color: #FFFFFF;
    background-color: {colors.primary};
    border-color: {colors.primary};
}}

.btn-primary:hover {{
    background-color: {self._darken_color(colors.primary, 0.1)};
    border-color: {self._darken_color(colors.primary, 0.1)};
}}

.btn-secondary {{
    color: #FFFFFF;
    background-color: {colors.secondary};
    border-color: {colors.secondary};
}}
""",
            'card': f"""
.card {{
    position: relative;
    display: flex;
    flex-direction: column;
    min-width: 0;
    word-wrap: break-word;
    background-color: #FFFFFF;
    background-clip: border-box;
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}}

.card-header {{
    padding: 1rem 1.25rem;
    margin-bottom: 0;
    background-color: rgba(0, 0, 0, 0.03);
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}}

.card-body {{
    flex: 1 1 auto;
    padding: 1.25rem;
}}
""",
            'form': f"""
.form-control {{
    display: block;
    width: 100%;
    padding: 0.375rem 0.75rem;
    font-family: {typography.font_family_body};
    font-size: {typography.font_size_base};
    font-weight: 400;
    line-height: {typography.line_height_base};
    color: {colors.text};
    background-color: #FFFFFF;
    background-clip: padding-box;
    border: 1px solid #D1D5DB;
    border-radius: 0.375rem;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}}

.form-control:focus {{
    color: {colors.text};
    background-color: #FFFFFF;
    border-color: {colors.primary};
    outline: 0;
    box-shadow: 0 0 0 0.2rem {self._lighten_color(colors.primary, 0.25)};
}}

.form-label {{
    display: inline-block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}}
"""
        }
    
    def _generate_css(self, colors: ColorScheme, typography: TypographySystem, spacing: Dict[str, str], components: Dict[str, str]) -> str:
        """완전한 CSS 생성"""
        
        css = f"""
/* Design System CSS */

/* Color Variables */
{colors.to_css_variables()}

/* Typography */
body {{
    font-family: {typography.font_family_body};
    font-size: {typography.font_size_base};
    line-height: {typography.line_height_base};
    color: var(--color-text);
    background-color: var(--color-background);
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: {typography.font_family_heading};
    font-weight: 700;
    line-height: 1.2;
    margin-top: 0;
    margin-bottom: 0.5rem;
}}
"""
        
        # 타이포그래피 스케일 추가
        scale = typography.generate_scale()
        heading_map = {'3xl': 'h1', '2xl': 'h2', 'xl': 'h3', 'lg': 'h4', 'base': 'h5', 'sm': 'h6'}
        
        for size_name, heading in heading_map.items():
            if size_name in scale:
                css += f"\n{heading} {{ font-size: {scale[size_name]}; }}"
        
        # 스페이싱 유틸리티
        css += "\n\n/* Spacing Utilities */\n"
        for name, value in spacing.items():
            css += f".m-{name} {{ margin: {value}; }}\n"
            css += f".p-{name} {{ padding: {value}; }}\n"
            css += f".mt-{name} {{ margin-top: {value}; }}\n"
            css += f".mb-{name} {{ margin-bottom: {value}; }}\n"
            css += f".ml-{name} {{ margin-left: {value}; }}\n"
            css += f".mr-{name} {{ margin-right: {value}; }}\n"
        
        # 컴포넌트 스타일 추가
        css += "\n/* Components */\n"
        for component_css in components.values():
            css += component_css + "\n"
        
        return css
    
    def _darken_color(self, hex_color: str, amount: float) -> str:
        """색상 어둡게"""
        rgb = self._hex_to_rgb(hex_color)
        hsv = colorsys.rgb_to_hsv(*[x/255.0 for x in rgb])
        hsv = (hsv[0], hsv[1], max(0, hsv[2] - amount))
        return self._hsv_to_hex(*hsv)
    
    def _lighten_color(self, hex_color: str, amount: float) -> str:
        """색상 밝게"""
        rgb = self._hex_to_rgb(hex_color)
        hsv = colorsys.rgb_to_hsv(*[x/255.0 for x in rgb])
        hsv = (hsv[0], hsv[1], min(1, hsv[2] + amount))
        return self._hsv_to_hex(*hsv)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """HEX를 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _hsv_to_hex(self, h: float, s: float, v: float) -> str:
        """HSV를 HEX로 변환"""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )

class UIUXDesignAgent:
    """UI/UX 디자인 에이전트"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.accessibility_analyzer = AccessibilityAnalyzer()
        self.responsive_analyzer = ResponsiveAnalyzer()
        self.design_system_generator = DesignSystemGenerator()
        
    async def analyze_and_improve(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """UI/UX 분석 및 개선"""
        
        print("🎨 UI/UX 디자인 분석을 시작합니다...")
        
        all_issues = []
        
        # 1. 현재 디자인 분석
        if 'html_files' in project_config:
            print("📄 HTML 접근성 분석 중...")
            for html_file in project_config['html_files']:
                issues = await self._analyze_html_file(html_file)
                all_issues.extend(issues)
        
        if 'css_files' in project_config:
            print("🎨 CSS 반응형 분석 중...")
            for css_file in project_config['css_files']:
                issues = await self._analyze_css_file(css_file)
                all_issues.extend(issues)
        
        # 2. 색상 대비 분석
        if 'color_combinations' in project_config:
            print("🔍 색상 대비 분석 중...")
            contrast_issues = self._analyze_color_contrasts(project_config['color_combinations'])
            all_issues.extend(contrast_issues)
        
        # 3. 성능 분석
        if 'lighthouse_results' in project_config:
            print("⚡ 성능 분석 중...")
            performance_issues = self._analyze_performance(project_config['lighthouse_results'])
            all_issues.extend(performance_issues)
        
        # 4. 디자인 시스템 생성
        design_system = None
        if project_config.get('generate_design_system', False):
            print("🎨 디자인 시스템 생성 중...")
            brand_color = project_config.get('brand_color', '#3B82F6')
            design_system = self.design_system_generator.generate_design_system(brand_color)
        
        # 5. 개선 사항 우선순위 결정
        prioritized_issues = self._prioritize_issues(all_issues)
        
        # 6. 자동 수정 생성
        fixes = []
        if project_config.get('auto_fix', False):
            print("🔧 자동 수정 생성 중...")
            fixes = await self._generate_fixes(prioritized_issues)
        
        # 7. 보고서 생성
        report = self._generate_design_report(
            prioritized_issues,
            fixes,
            design_system,
            project_config
        )
        
        print("✅ UI/UX 디자인 분석이 완료되었습니다!")
        
        return report
    
    async def _analyze_html_file(self, file_path: str) -> List[DesignIssue]:
        """HTML 파일 분석"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            
            return await self.accessibility_analyzer.analyze_html(content)
        except Exception as e:
            print(f"HTML 파일 분석 오류 {file_path}: {e}")
            return []
    
    async def _analyze_css_file(self, file_path: str) -> List[DesignIssue]:
        """CSS 파일 분석"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            
            return await self.responsive_analyzer.analyze_css(content)
        except Exception as e:
            print(f"CSS 파일 분석 오류 {file_path}: {e}")
            return []
    
    def _analyze_color_contrasts(self, color_combinations: List[Dict[str, str]]) -> List[DesignIssue]:
        """색상 대비 분석"""
        issues = []
        
        for combo in color_combinations:
            result = self.accessibility_analyzer.check_color_contrast(
                combo['foreground'],
                combo['background'],
                combo.get('font_size', 16),
                combo.get('is_bold', False)
            )
            
            if not result['passes_aa']:
                issues.append(DesignIssue(
                    issue_type=DesignIssueType.COLOR_CONTRAST,
                    severity='high' if result['contrast_ratio'] < 3.0 else 'medium',
                    element=combo.get('element', 'unknown'),
                    description='불충분한 색상 대비',
                    current_value=f"대비율 {result['contrast_ratio']}:1",
                    recommended_value=f"최소 {result['required_aa']}:1 필요",
                    wcag_criterion='1.4.3',
                    impact='텍스트 가독성 저하',
                    auto_fixable=True
                ))
        
        return issues
    
    def _analyze_performance(self, lighthouse_results: Dict[str, Any]) -> List[DesignIssue]:
        """성능 분석"""
        issues = []
        
        # 성능 점수 분석
        if lighthouse_results.get('performance', 100) < 90:
            issues.append(DesignIssue(
                issue_type=DesignIssueType.PERFORMANCE,
                severity='medium',
                element='overall',
                description='성능 점수가 낮음',
                current_value=f"{lighthouse_results['performance']}/100",
                recommended_value='90/100 이상',
                impact='사용자 경험 저하',
                auto_fixable=False
            ))
        
        # 접근성 점수 분석
        if lighthouse_results.get('accessibility', 100) < 90:
            issues.append(DesignIssue(
                issue_type=DesignIssueType.ACCESSIBILITY,
                severity='high',
                element='overall',
                description='접근성 점수가 낮음',
                current_value=f"{lighthouse_results['accessibility']}/100",
                recommended_value='90/100 이상',
                wcag_criterion='Multiple',
                impact='접근성 저하',
                auto_fixable=False
            ))
        
        return issues
    
    def _prioritize_issues(self, issues: List[DesignIssue]) -> List[DesignIssue]:
        """이슈 우선순위 결정"""
        
        severity_score = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        # 접근성 이슈에 가중치 부여
        def issue_score(issue: DesignIssue) -> float:
            base_score = severity_score.get(issue.severity, 0)
            
            # 접근성 이슈는 1.5배 가중치
            if issue.issue_type == DesignIssueType.ACCESSIBILITY:
                base_score *= 1.5
            
            # 자동 수정 가능한 경우 약간 낮은 우선순위
            if issue.auto_fixable:
                base_score *= 0.9
            
            return base_score
        
        return sorted(issues, key=issue_score, reverse=True)
    
    async def _generate_fixes(self, issues: List[DesignIssue]) -> List[Dict[str, Any]]:
        """자동 수정 생성"""
        fixes = []
        
        for issue in issues:
            if issue.auto_fixable:
                fix = None
                
                if issue.issue_type == DesignIssueType.COLOR_CONTRAST:
                    fix = self._generate_color_contrast_fix(issue)
                elif issue.issue_type == DesignIssueType.RESPONSIVE:
                    fix = self._generate_responsive_fix(issue)
                elif issue.issue_type == DesignIssueType.ACCESSIBILITY:
                    fix = self._generate_accessibility_fix(issue)
                
                if fix:
                    fixes.append(fix)
        
        return fixes
    
    def _generate_color_contrast_fix(self, issue: DesignIssue) -> Dict[str, Any]:
        """색상 대비 수정 생성"""
        # 간단한 예시: 텍스트 색상을 더 어둡게
        return {
            'issue_id': id(issue),
            'type': 'color_adjustment',
            'element': issue.element,
            'original': issue.current_value,
            'fixed': 'color: #1A1A1A; /* 대비율 개선 */',
            'css': f"""
/* 색상 대비 개선 */
{issue.element} {{
    color: #1A1A1A; /* WCAG AA 기준 충족 */
}}
"""
        }
    
    def _generate_responsive_fix(self, issue: DesignIssue) -> Dict[str, Any]:
        """반응형 수정 생성"""
        if 'media-queries' in issue.element:
            # 누락된 미디어 쿼리 추가
            return {
                'issue_id': id(issue),
                'type': 'media_query',
                'element': issue.element,
                'original': issue.current_value,
                'fixed': issue.recommended_value,
                'css': f"""
/* 반응형 미디어 쿼리 추가 */
{issue.recommended_value} {{
    /* 디바이스별 스타일 */
    .container {{
        padding: 1rem;
    }}
}}
"""
            }
        elif 'fixed-width' in issue.element:
            # 고정 너비를 상대적 단위로 변경
            return {
                'issue_id': id(issue),
                'type': 'relative_units',
                'element': issue.element,
                'original': issue.current_value,
                'fixed': 'width: 100%; max-width: ' + issue.current_value,
                'css': f"""
/* 고정 너비를 반응형으로 변경 */
.element {{
    width: 100%;
    max-width: {issue.current_value};
}}
"""
            }
        
        return None
    
    def _generate_accessibility_fix(self, issue: DesignIssue) -> Dict[str, Any]:
        """접근성 수정 생성"""
        if 'label' in issue.description.lower():
            # 누락된 레이블 추가
            return {
                'issue_id': id(issue),
                'type': 'add_label',
                'element': issue.element,
                'original': issue.current_value,
                'fixed': '<label for="input-id">Label Text</label>',
                'html': f"""
<!-- 접근성을 위한 레이블 추가 -->
<label for="{issue.element.replace('#', '')}">
    필드 레이블
</label>
"""
            }
        
        return None
    
    def _generate_design_report(
        self,
        issues: List[DesignIssue],
        fixes: List[Dict[str, Any]],
        design_system: Optional[Dict[str, Any]],
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """디자인 분석 보고서 생성"""
        
        # 이슈 통계
        issue_stats = {
            'total': len(issues),
            'by_type': {},
            'by_severity': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        
        for issue in issues:
            # 유형별
            issue_type = issue.issue_type.value
            if issue_type not in issue_stats['by_type']:
                issue_stats['by_type'][issue_type] = 0
            issue_stats['by_type'][issue_type] += 1
            
            # 심각도별
            issue_stats['by_severity'][issue.severity] += 1
        
        # 점수 계산
        design_score = self._calculate_design_score(issues)
        
        report = {
            'summary': {
                'design_score': design_score,
                'total_issues': len(issues),
                'critical_issues': issue_stats['by_severity']['critical'],
                'auto_fixes_available': len(fixes),
                'accessibility_score': self._calculate_accessibility_score(issues)
            },
            'issue_statistics': issue_stats,
            'top_issues': issues[:10],
            'improvement_recommendations': self._generate_recommendations(issues),
            'fixes': fixes,
            'design_system': design_system,
            'generated_at': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        self._save_report(report)
        
        return report
    
    def _calculate_design_score(self, issues: List[DesignIssue]) -> float:
        """디자인 점수 계산 (0-100)"""
        
        if not issues:
            return 100.0
        
        # 이슈별 감점
        deductions = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 0.5
        }
        
        total_deduction = sum(deductions.get(issue.severity, 0) for issue in issues)
        
        # 최소 0점
        score = max(0, 100 - total_deduction)
        
        return round(score, 1)
    
    def _calculate_accessibility_score(self, issues: List[DesignIssue]) -> float:
        """접근성 점수 계산"""
        
        accessibility_issues = [i for i in issues if i.issue_type == DesignIssueType.ACCESSIBILITY]
        
        if not accessibility_issues:
            return 100.0
        
        # WCAG 레벨별 감점
        total_deduction = len(accessibility_issues) * 5
        
        return max(0, 100 - total_deduction)
    
    def _generate_recommendations(self, issues: List[DesignIssue]) -> List[str]:
        """개선 권장사항 생성"""
        
        recommendations = []
        
        # 이슈 유형별 권장사항
        issue_types = set(issue.issue_type for issue in issues)
        
        if DesignIssueType.ACCESSIBILITY in issue_types:
            recommendations.append("WCAG 2.1 AA 기준 준수를 위한 접근성 감사 실시")
        
        if DesignIssueType.COLOR_CONTRAST in issue_types:
            recommendations.append("모든 텍스트 요소의 색상 대비율 검토 및 개선")
        
        if DesignIssueType.RESPONSIVE in issue_types:
            recommendations.append("모바일 우선 반응형 디자인 전략 적용")
        
        if DesignIssueType.PERFORMANCE in issue_types:
            recommendations.append("이미지 최적화 및 지연 로딩 구현")
        
        # 일반 권장사항
        recommendations.extend([
            "일관된 디자인 시스템 구축 및 유지",
            "정기적인 사용성 테스트 실시",
            "접근성 자동화 테스트를 CI/CD에 통합",
            "디자인 토큰을 활용한 일관성 유지",
            "사용자 피드백 수집 및 반영 프로세스 구축"
        ])
        
        return recommendations[:8]
    
    def _save_report(self, report: Dict[str, Any]):
        """보고서 저장"""
        
        # JSON 보고서
        with open('design_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # 마크다운 보고서
        self._generate_markdown_report(report)
        
        # 디자인 시스템 CSS
        if report.get('design_system'):
            with open('design-system.css', 'w') as f:
                f.write(report['design_system']['css'])
    
    def _generate_markdown_report(self, report: Dict[str, Any]):
        """마크다운 보고서 생성"""
        
        markdown = f"""# 🎨 UI/UX 디자인 분석 보고서

**생성일시**: {report['generated_at']}

## 📊 요약

- **디자인 점수**: {report['summary']['design_score']}/100
- **접근성 점수**: {report['summary']['accessibility_score']}/100
- **발견된 이슈**: {report['summary']['total_issues']}개
- **심각한 이슈**: {report['summary']['critical_issues']}개
- **자동 수정 가능**: {report['summary']['auto_fixes_available']}개

## 📈 이슈 분포

### 유형별
"""
        
        for issue_type, count in report['issue_statistics']['by_type'].items():
            markdown += f"- {issue_type}: {count}개\n"
        
        markdown += """
### 심각도별
"""
        
        for severity, count in report['issue_statistics']['by_severity'].items():
            if count > 0:
                markdown += f"- {severity.upper()}: {count}개\n"
        
        markdown += """
## 🔍 주요 발견 사항

"""
        
        for i, issue in enumerate(report['top_issues'][:5], 1):
            markdown += f"""
### {i}. {issue['description']}
- **유형**: {issue['issue_type']}
- **심각도**: {issue['severity']}
- **요소**: {issue['element']}
- **현재**: {issue['current_value']}
- **권장**: {issue['recommended_value']}
"""
            if issue.get('wcag_criterion'):
                markdown += f"- **WCAG 기준**: {issue['wcag_criterion']}\n"
        
        markdown += """
## 💡 개선 권장사항

"""
        
        for rec in report['improvement_recommendations']:
            markdown += f"- {rec}\n"
        
        if report.get('design_system'):
            markdown += """
## 🎨 생성된 디자인 시스템

디자인 시스템이 성공적으로 생성되었습니다.
- 파일: `design-system.css`
- 색상 스킴, 타이포그래피, 스페이싱, 컴포넌트 포함
"""
        
        with open('design_report.md', 'w') as f:
            f.write(markdown)

# 사용 예시
async def main():
    agent = UIUXDesignAgent('configs/agents/ui-ux-design-agent.yaml')
    
    project_config = {
        'project_name': 'MyWebApp',
        'html_files': [
            'public/index.html',
            'public/about.html'
        ],
        'css_files': [
            'public/css/styles.css',
            'public/css/components.css'
        ],
        'color_combinations': [
            {
                'element': '.primary-text',
                'foreground': '#666666',
                'background': '#FFFFFF',
                'font_size': 16
            },
            {
                'element': '.button-primary',
                'foreground': '#FFFFFF',
                'background': '#3B82F6',
                'font_size': 14,
                'is_bold': True
            }
        ],
        'lighthouse_results': {
            'performance': 85,
            'accessibility': 78,
            'best_practices': 92,
            'seo': 90
        },
        'generate_design_system': True,
        'brand_color': '#3B82F6',
        'auto_fix': True
    }
    
    report = await agent.analyze_and_improve(project_config)
    print(f"\n✅ UI/UX 디자인 분석 완료!")
    print(f"🎨 디자인 점수: {report['summary']['design_score']}/100")
    print(f"♿ 접근성 점수: {report['summary']['accessibility_score']}/100")
    print(f"🔧 자동 수정 가능: {report['summary']['auto_fixes_available']}개")
    print(f"\n📄 상세 보고서: design_report.md")
    
    if report.get('design_system'):
        print(f"🎨 디자인 시스템: design-system.css")

if __name__ == "__main__":
    asyncio.run(main())