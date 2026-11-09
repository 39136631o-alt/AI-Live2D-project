import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'web/assets/character'


def test_layer_assets_and_metadata():
    manifest = json.loads((ASSETS / 'manifest.json').read_text())
    assert manifest['official_cubism_model'] is False
    assert len(manifest['layers']) == 27
    assert {layer['id'] for layer in manifest['layers']} >= {
        'hair_front','hair_back','face','eye_left','eye_right','brow_left','brow_right',
        'mouth','body','arm_left','arm_right','costume_bodice','costume_skirt'}
    composite = Image.new('RGBA',(600,1100))
    for index, layer in enumerate(manifest['layers']):
        data = (ASSETS/layer['svg']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == layer['sha256']
        assert layer['order'] == index
        document = ET.fromstring(data)
        assert document.attrib['viewBox'] == '0 0 600 1100'
        with Image.open(ASSETS/layer['png']) as image:
            assert image.mode == 'RGBA' and image.size == (600,1100)
            assert image.getchannel('A').getbbox() is not None
            composite = Image.alpha_composite(composite,image)
    with Image.open(ASSETS/'character.png') as image:
        # Individually rasterized antialiasing can differ slightly at overlapping edges.
        diff = ImageChops.difference(composite,image)
        assert sum(sum(channel.getdata()) for channel in diff.split())/(600*1100*4) < 1
        assert image.getchannel('A').getextrema() == (0,255)


def test_required_animation_nodes_and_no_remote_assets():
    source = (ASSETS/'character.svg').read_text()
    document = ET.fromstring(source)
    ids = [node.attrib['id'] for node in document.iter() if 'id' in node.attrib]
    assert len(ids) == len(set(ids))
    assert {'mouth_open','mouth_closed','eye_open_left','eye_closed_right'} <= set(ids)
    assert '<script' not in source and '<image' not in source and 'href=' not in source
    assert not list(ASSETS.rglob('*.moc3'))


def test_build_is_reproducible(tmp_path):
    spec = importlib.util.spec_from_file_location('build_character',ROOT/'tools/build_character.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.build(tmp_path, png=False)
    assert (tmp_path/'character.svg').read_bytes() == (ASSETS/'character.svg').read_bytes()
    assert result['master_sha256'] == hashlib.sha256((ASSETS/'character.svg').read_bytes()).hexdigest()
