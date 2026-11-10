"""Real Chromium smoke tests. WebKit is opt-in via CHARACTER_BROWSER=webkit."""
import functools
import http.server
import os
from pathlib import Path
import threading

import pytest

playwright = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def url():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            prefix = '/AI-Live2D-project/'
            if self.path.startswith(prefix):
                self.path = '/' + self.path[len(prefix):]
            return super().do_GET()

        def log_message(self, *args):
            pass
    handler = functools.partial(QuietHandler, directory=str(ROOT/'web'))
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture(scope='module')
def browser():
    with playwright.sync_playwright() as p:
        engine = os.environ.get('CHARACTER_BROWSER','chromium')
        kwargs = {'headless':True}
        if engine == 'chromium':
            kwargs.update(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
        instance = getattr(p,engine).launch(**kwargs)
        yield instance
        instance.close()


def ready(browser,url,**options):
    context = browser.new_context(**options)
    page = context.new_page()
    errors = []
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url)
    page.wait_for_function('Boolean(window.character)')
    return context,page,errors


def test_desktop_animation_and_pause(browser,url):
    context,page,errors = ready(browser,url,viewport={'width':1440,'height':1100})
    try:
        assert page.locator('[data-rig]').count() == 27
        head = page.locator('#face').get_attribute('transform')
        hair = page.locator('#hair_side_left').get_attribute('transform')
        page.wait_for_function("Number(document.querySelector('svg').dataset.eyeOpen)<.2")
        assert page.locator('#face').get_attribute('transform') != head
        assert page.locator('#hair_side_left').get_attribute('transform') != hair
        page.get_by_label('說話口型',exact=True).check()
        page.wait_for_function("Number(document.querySelector('svg').dataset.mouthOpen)>.4")
        page.locator('#pause').click()
        before = page.locator('#character-host').inner_html()
        page.wait_for_timeout(300)
        assert page.locator('#character-host').inner_html() == before
        page.locator('#pause').click()
        page.wait_for_timeout(100)
        assert page.locator('#character-host').inner_html() != before
        assert not errors
    finally:
        context.close()


def test_manual_extremes_and_expression(browser,url):
    context,page,errors = ready(browser,url)
    try:
        for key,value in [('eyeOpen','0'),('mouthOpen','1'),('headAngle','5'),('breath','1'),('hairSway','-4')]:
            page.locator(f'#{key}').fill(value)
        assert page.locator('#eye_open_left').get_attribute('opacity') == '0'
        assert page.locator('#eye_closed_left').get_attribute('opacity') == '1'
        assert page.locator('#mouth_open').get_attribute('opacity') == '1'
        assert 'rotate(5.0000' in page.locator('#face').get_attribute('transform')
        assert page.get_by_label('頭部微擺',exact=True).is_checked() is False
        page.get_by_role('button',name='驚訝',exact=True).click()
        assert page.locator('#character-host svg').get_attribute('data-expression') == 'surprised'
        page.locator('#reset').click()
        assert page.locator('#mouthOpen').input_value() == '0'
        assert page.get_by_label('頭部微擺',exact=True).is_checked()
        assert not errors
    finally:
        context.close()


def test_mobile_touch_keyboard_and_layout(browser,url):
    context,page,errors = ready(browser,url,viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2)
    try:
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('#character-host').tap(position={'x':180,'y':190})
        assert page.locator('#greeting').inner_text() == '你好，很高興見到你。'
        assert 'visible' in page.locator('#greeting').get_attribute('class')
        assert page.locator('#character-host svg').get_attribute('data-expression') == 'happy'
        page.locator('#character-host').focus()
        page.keyboard.press('Enter')
        assert page.locator('#greeting').is_visible()
        page.locator('#reset').click()
        assert 'visible' not in page.locator('#greeting').get_attribute('class')
        (ROOT/'outputs').mkdir(exist_ok=True)
        page.screenshot(path=str(ROOT/'outputs/mobile-preview.png'),full_page=True)
        assert not errors
    finally:
        context.close()


def test_reduced_motion_and_failed_asset(browser,url):
    context,page,errors = ready(browser,url,reduced_motion='reduce')
    try:
        assert not page.get_by_label('頭部微擺',exact=True).is_checked()
        assert not page.get_by_label('髮絲慣性',exact=True).is_checked()
        assert not page.get_by_label('呼吸起伏',exact=True).is_checked()
        assert not errors
    finally:
        context.close()
    context = browser.new_context()
    page = context.new_page()
    page.route('**/character.svg',lambda route:route.fulfill(status=404,body='missing'))
    page.goto(url)
    page.wait_for_function("document.querySelector('#app-status').textContent.startsWith('載入失敗')")
    assert page.locator('#pause').is_disabled()
    context.close()


def test_pages_project_subpath_and_all_animation_channels(browser,url):
    context,page,errors = ready(browser,url+'/AI-Live2D-project/',viewport={'width':390,'height':844},has_touch=True,is_mobile=True)
    try:
        assert page.locator('[data-rig]').count() == 27
        # Isolate breathing: body transform must change without head movement.
        page.evaluate("character.setOptions({blink:false,talk:false,breathe:true,sway:false,hair:false})")
        before = page.locator('#body').get_attribute('transform')
        page.wait_for_function("document.querySelector('#body').getAttribute('transform') !== " + repr(before))
        # Verify automatic blink and talking from the hosted project subdirectory.
        page.evaluate("character.setOptions({blink:true,talk:true,sway:true,hair:true})")
        page.wait_for_function("Number(document.querySelector('svg').dataset.eyeOpen)<.2")
        page.wait_for_function("Number(document.querySelector('svg').dataset.mouthOpen)>.3")
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('#character-host').tap(position={'x':180,'y':190})
        assert 'visible' in page.locator('#greeting').get_attribute('class')
        assert page.locator('#character-host svg').get_attribute('data-expression') == 'happy'
        assert not errors
    finally:
        context.close()


def test_stage_two_fps_reactions_and_cache(browser,url):
    context,page,errors=ready(browser,url,viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    try:
        page.wait_for_function("/\\d+\\.\\d FPS/.test(document.querySelector('#fps-value').textContent)")
        fps=page.locator('#fps-value').inner_text()
        assert float(fps.split()[0])>0
        page.get_by_role('button',name='揮手',exact=True).click()
        page.wait_for_function('Math.abs(character.waveAngle)>35')
        page.get_by_role('button',name='驚訝互動',exact=True).click()
        assert page.locator('svg').get_attribute('data-expression')=='surprised'
        page.get_by_role('button',name='微笑互動',exact=True).click()
        assert page.locator('svg').get_attribute('data-expression')=='happy'
        # Face nodes are cached: rendering must not issue selector queries.
        page.evaluate("""() => {
          character.svg.querySelector=()=>{throw new Error('Per-frame selector');};
          character.render();
          delete character.svg.querySelector;
        }""")
        page.locator('#pause').click()
        assert page.locator('#fps-value').inner_text()=='暫停'
        before=page.locator('#character-host').inner_html()
        page.wait_for_timeout(150)
        assert before==page.locator('#character-host').inner_html()
        page.locator('#reset').click()
        assert page.get_by_label('待機連動',exact=True).is_checked()
        assert not errors
    finally:
        context.close()


def test_joint_coverage_during_extreme_pose(browser,url):
    context,page,errors=ready(browser,url)
    try:
        page.locator('#headAngle').fill('5')
        page.locator('#hairSway').fill('4')
        page.get_by_role('button',name='揮手',exact=True).click()
        page.wait_for_function('Math.abs(character.waveAngle)>40')
        page.evaluate('character.setPaused(true)')
        coverage=page.evaluate('''async () => {
          const svg=character.svg;
          const matrix=svg.getCTM().inverse().multiply(svg.querySelector('#body').getCTM());
          const points=[[225,260],[375,260],[300,210],[280,460]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(matrix));
          const image=new Image();
          const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'});
          const url=URL.createObjectURL(blob);
          try {
            await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});
            const canvas=document.createElement('canvas');canvas.width=600;canvas.height=1100;
            const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0,600,1100);
            return points.map(p=>ctx.getImageData(Math.round(p.x),Math.round(p.y),1,1).data[3]);
          } finally {URL.revokeObjectURL(url);}
        }''')
        assert min(coverage)>245,coverage
        assert not errors
    finally:
        context.close()


def test_eye_expression_quality_and_blink_alignment(browser,url):
    context,page,errors=ready(browser,url)
    try:
        assert page.locator('svg').get_attribute('data-expression')=='happy'
        page.evaluate("character.setOptions({blink:false,talk:false,breathe:false,sway:false,hair:false,idle:false});character.setPaused(true)")
        iris=page.locator('#iris_left')
        fixed=iris.evaluate('node=>({bbox:node.getBBox().toJSON?.()??[node.getBBox().x,node.getBBox().y,node.getBBox().width,node.getBBox().height],matrix:node.getCTM().toString()})')
        paths=[]
        for expression in ['happy','closedSmile','halfLidded']:
            page.evaluate('(name)=>character.setExpression(name)',expression)
            paths.append(page.locator('#eye_aperture_left').get_attribute('d'))
            if expression=='closedSmile':
                assert page.locator('#eye_open_left').get_attribute('opacity')=='0'
                assert page.locator('#eye_closed_left').get_attribute('opacity')=='1'
            else:
                assert page.locator('#eye_open_left').get_attribute('opacity')=='1'
        assert len(set(paths))==3
        page.evaluate("character.setExpression('happy')")
        # Scan a full blink: the pupil remains fixed while aperture and eye whites agree.
        for value in [1,.75,.5,.25,.01,0,.25,.5,.75,1]:
            page.evaluate('(v)=>character.setParameter("eyeOpen",v)',value)
            assert page.locator('#eye_white_left').get_attribute('d')==page.locator('#eye_aperture_left').get_attribute('d')
            assert iris.get_attribute('transform') is None
            assert iris.evaluate('node=>({bbox:node.getBBox().toJSON?.()??[node.getBBox().x,node.getBBox().y,node.getBBox().width,node.getBBox().height],matrix:node.getCTM().toString()})')==fixed
            assert page.locator('#eye_open_left').get_attribute('transform') is None
        assert not errors
    finally:
        context.close()
