"""Run from the repository root: cloud Chromium cadence, not an iPhone benchmark."""
import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory='web'))
threading.Thread(target=s.serve_forever,daemon=True).start()
Path('outputs').mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2)
 page.goto(f'http://127.0.0.1:{s.server_port}')
 page.wait_for_function('Boolean(window.character)')
 page.evaluate('''() => {
  window.timings=[];window.cadence=[];
  const render=character.render.bind(character);
  character.render=()=>{const start=performance.now();render();timings.push(performance.now()-start);};
  character.addEventListener('performance',event=>{if(event.detail.fps!==null)cadence.push(event.detail.fps);});
 }''')
 page.wait_for_timeout(4000)
 report=page.evaluate('''() => {
  const values=timings.slice().sort((a,b)=>a-b);
  return {engine:navigator.userAgent,viewport:[innerWidth,innerHeight],frames:values.length,
    fps_samples:cadence,render_ms_median:values[Math.floor(values.length*.5)],render_ms_p95:values[Math.floor(values.length*.95)]};
 }''')
 page.get_by_role('button',name='揮手',exact=True).click()
 page.wait_for_function('Math.abs(character.waveAngle)>65')
 page.evaluate('character.setPaused(true)')
 page.locator('#character-host').scroll_into_view_if_needed()
 page.screenshot(path='outputs/stage-two-wave.png',full_page=True)
 report['joint_wave_angle']=page.evaluate('character.waveAngle')
 print(json.dumps(report,indent=2));Path('outputs/stage-two-performance.json').write_text(json.dumps(report,indent=2))
 b.close()
s.shutdown()
