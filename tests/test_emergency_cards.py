"""Validate the priority and destinations of the two emergency cards without dialing."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.href = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')

    def handle_data(self, text):
        if self.href:
            self.rows.append((self.href, text.strip()))

    def handle_endtag(self, tag):
        if tag == 'a':
            self.href = None


def card(name):
    return re.search(r'<div class="mini" id="' + name + r'">(.*?)</div>', HTML, re.S)[1]


class EmergencyCards(unittest.TestCase):
    def test_water_rescue_calls_before_assessment_and_no_side_position_instruction(self):
        text = card('afogamento')
        self.assertEqual(Links(text).rows, [('tel:193', 'Bombeiros 193')])
        ordered = ['Chame os guarda-vidas', 'tel:193', 'Não entre na água',
                   'fora da água', 'responde e se respira normalmente', 'siga as instruções',
                   'procure avaliação médica']
        self.assertEqual(sorted(ordered, key=text.index), ordered)
        self.assertNotRegex(text, r'lateral|de lado|quase afogamento')

    def test_heat_calls_before_cooling_and_no_drinking_with_altered_consciousness(self):
        text = card('calor-intenso')
        self.assertEqual(Links(text).rows, [('tel:192', 'SAMU 192')])
        self.assertLess(text.index('tel:192'), text.index('panos molhados e frios'))
        self.assertIn('confusão, desmaio ou convulsões', text)
        self.assertIn('Não ofereça líquidos se ela estiver confusa, sonolenta ou inconsciente', text)
        self.assertIn('Siga as instruções do atendente', text)

    def test_landing_has_visible_keyboard_ready_native_links_before_sos(self):
        top = HTML.split('<main>', 1)[1].split('</div>', 1)[0]
        links = [pair for pair in Links(top).rows if pair[0].startswith('tel:')]
        self.assertEqual(links, [('tel:193', 'Bombeiros 193'), ('tel:192', 'SAMU 192')])
        self.assertLess(top.index('tel:192'), top.index('https://acarolmourad-commits.github.io/asf-sos/'))
        self.assertEqual(HTML.count('href="tel:193"'), 3)
        self.assertEqual(HTML.count('href="tel:192"'), 3)
        markup = re.findall(r'<a[^>]+href="tel:[^"]+"[^>]*>', HTML)
        self.assertTrue(all('onclick' not in x and 'tabindex' not in x for x in markup))
        self.assertIn('.emergency-number:focus-visible', HTML)
        self.assertIn('min-height:24px', HTML)
