"""Original procedural vector redraw guided by the user-provided design board.
No pixels, textures, fonts, or model weights are copied from third-party assets.
All layers share a 600x1100 canvas; concealed joints are deliberately overdrawn.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

W, H = 600, 1100
DEFS = '''<defs>
<linearGradient id="hair" x1="0" y1="0" x2=".85" y2="1" gradientUnits="objectBoundingBox"><stop stop-color="#fffafc"/><stop offset=".45" stop-color="#e1dce9"/><stop offset=".7" stop-color="#bdb6d4"/><stop offset="1" stop-color="#f7f1ff"/></linearGradient>
<linearGradient id="silk" x2=".8" y2="1"><stop stop-color="#ffffff"/><stop offset=".55" stop-color="#eee8fa"/><stop offset="1" stop-color="#a99acb"/></linearGradient>
<linearGradient id="violet" x2="1" y2="1"><stop stop-color="#a99bce"/><stop offset=".45" stop-color="#71628f"/><stop offset="1" stop-color="#45415e"/></linearGradient>
<linearGradient id="dark" x2="1" y2=".8"><stop stop-color="#272636"/><stop offset=".5" stop-color="#464052"/><stop offset="1" stop-color="#242333"/></linearGradient>
<linearGradient id="skin" x2=".7" y2="1"><stop stop-color="#fff1ed"/><stop offset=".65" stop-color="#f7d9d4"/><stop offset="1" stop-color="#e5b7bf"/></linearGradient>
<linearGradient id="iris" x2="0" y2="1"><stop stop-color="#4e376d"/><stop offset=".5" stop-color="#9671b4"/><stop offset="1" stop-color="#e6b8ed"/></linearGradient>
<radialGradient id="blush"><stop stop-color="#eaa2b4" stop-opacity=".55"/><stop offset="1" stop-color="#eaa2b4" stop-opacity="0"/></radialGradient>
</defs>'''


def path(d, fill, stroke="#74677e", width=1.7, extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def ellipse(x, y, rx, ry, fill, extra=""):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'


def jewel(x, y, size=8):
    return path(f'M{x} {y-size} L{x+size*.65} {y} {x} {y+size} {x-size*.65} {y}Z', '#d9c3ec', '#c8b593', 1.5) + path(f'M{x} {y-size+2} V{y+size-2}', 'none', '#fff6e3', .8)


def flower(x, y, scale=1):
    petals = ''
    for i in range(7):
        a = i * 360 / 7
        petals += path(f'M0 0 Q-15 -18 0 -37 Q15 -18 0 0Z', 'url(#silk)', '#a092b8', 1, f'transform="rotate({a})"')
    return f'<g transform="translate({x} {y}) scale({scale})">{petals}{ellipse(0,0,8,8,"#dbc79d")}{jewel(0,0,6)}</g>'


def svg(content):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="1100" viewBox="0 0 600 1100">{DEFS}{content}</svg>'


def make_layers():
    layers = []
    def add(name, label, rig, pivot, content, notes=""):
        layers.append(dict(id=name, label=label, rig=rig, pivot=pivot, content=content, notes=notes))
    # Behind the body: long continuous hair cap and both long locks.
    add('hair_back', '後髮・完整髮底', 'head', [300, 218],
        path('M242 91 Q300 29 357 89 Q392 155 373 264 Q375 362 424 452 Q468 534 419 629 Q425 575 387 538 Q414 666 360 749 Q382 651 345 581 Q303 607 259 572 Q220 686 238 759 Q176 679 209 568 Q168 622 155 657 Q175 563 179 499 Q136 428 201 332 Q221 280 215 198 Q205 126 242 91Z', 'url(#hair)') +
        path('M242 176 Q224 303 205 411 T225 671 M351 172 Q372 308 396 426 T379 665 M231 275 Q181 393 192 479 M363 268 Q424 405 413 503', 'none', '#aaa0bf', 1.5),
        '完整後髮輪廓，身體後方仍有填色；非從平面圖裁切。')
    add('hair_back_left', '後髮左長束', 'hairBackL', [234, 180],
        path('M239 183 Q234 285 191 363 Q132 461 184 534 Q205 562 187 604 Q232 563 207 510 Q174 461 220 401 Q277 310 263 201Z', 'url(#hair)') + path('M248 210 Q240 332 204 390 Q161 463 199 524', 'none', '#f9f3ff', 4))
    add('hair_back_right', '後髮右長束', 'hairBackR', [361, 180],
        path('M350 187 Q376 273 399 322 Q459 410 429 478 Q409 516 444 553 Q384 532 397 479 Q425 414 371 358 Q338 294 336 201Z', 'url(#hair)') + path('M354 215 Q372 317 401 363 T413 479', 'none', '#f8f2ff', 4))
    add('costume_train', '白紫後裙與長飄帶', 'body', [300, 449],
        path('M238 417 Q205 472 177 589 L141 905 L220 847 L252 910 L298 600 L362 911 L394 845 L476 936 Q419 718 397 592 Q383 486 361 422Z', 'url(#violet)') +
        path('M240 448 L180 848 L210 815 L231 847 L282 495 M359 448 L425 866 L399 832 L378 867 L320 497', 'url(#silk)', '#d6c8e3', 2) +
        path('M206 530 Q177 730 158 876 M386 535 Q425 750 460 906', 'none', '#c3b193', 2))
    add('body', '身體・完整頸肩軀幹', 'body', [300, 449],
        path('M278 193 L322 193 Q319 221 334 232 Q355 235 375 254 L365 305 Q342 335 337 392 L349 467 Q302 499 250 467 L265 389 Q257 333 235 305 L223 255 Q243 238 265 233 Q280 222 278 193Z', 'url(#skin)'),
        '頸部延伸到臉後方、雙肩和腰臀在服裝下完整延伸，作為活動遮擋補圖。')
    add('leg_left', '角色右腿・淺襪', 'static', [276, 498],
        path('M252 471 Q283 466 291 499 L286 697 Q285 724 274 753 L265 985 Q253 1000 237 982 L236 759 Q225 735 230 699 L232 530Z', 'url(#skin)') +
        path('M231 577 Q259 584 288 579 L286 699 Q284 725 274 753 L265 986 Q250 1001 237 985 L236 759 Q224 735 230 699Z', '#c9bfda', '#8b7f9c') +
        path('M236 584 Q260 593 287 584 L287 601 Q261 609 233 600Z', 'url(#dark)') + jewel(260,594,7))
    add('leg_right', '角色左腿・深色長襪', 'static', [330, 498],
        path('M310 494 Q333 466 358 489 L369 699 Q376 729 364 756 L362 987 Q345 1000 331 985 L325 758 Q310 735 314 701Z', 'url(#skin)') +
        path('M311 543 Q338 554 362 544 L369 699 Q376 729 364 756 L362 987 Q345 1000 331 985 L325 758 Q310 735 314 701Z', 'url(#dark)') +
        path('M311 551 Q337 564 363 551 M327 755 L341 972', 'none', '#82768f', 2) + jewel(338,560,7))
    for side, x in [('left', 251), ('right', 347)]:
        add(f'boot_{side}', '黑金短靴', 'static', [x, 972],
            path(f'M{x-15} 916 L{x} 930 L{x+15} 916 L{x+12} 988 Q{x+32} 1015 {x+16} 1024 Q{x} 1032 {x-23} 1020 L{x-19} 994Z', 'url(#dark)', '#c4ad8e', 2) +
            path(f'M{x} 935 L{x-6} 970 L{x+2} 994 L{x-8} 1022 M{x-13} 956 L{x+11} 972 M{x-13} 977 L{x+9} 993', 'none', '#d7c2a0', 1.5) + jewel(x,946,8))
    # Arms include hidden shoulder caps and individually drawn fingers.
    arm = path('M225 250 Q242 245 247 270 L230 347 Q218 379 212 425 L196 458 Q187 465 184 452 L192 420 Q198 372 207 342 L210 275Z', 'url(#skin)') + path('M195 425 L185 453 M201 431 L192 461 M206 432 L200 455', 'none', '#c18f9f', 1)
    add('arm_left', '角色右手臂與手', 'armL', [225, 260], arm)
    add('arm_right', '角色左手臂與手', 'armR', [375, 260], f'<g transform="translate(600 0) scale(-1 1)">{arm}</g>')
    sleeve = path('M209 261 Q229 274 249 268 L237 299 L222 337 L238 362 L213 390 L191 364 L181 335 L199 299Z', 'url(#silk)') + path('M201 300 L212 319 L195 355 L213 378 L223 363 L215 343 L229 301', 'url(#violet)', '#b5a5c7', 1) + path('M211 270 L202 287 L214 282 L221 294 L233 276', 'url(#silk)') + jewel(217,295,6)
    add('sleeve_left', '角色右側露肩袖', 'armL', [225, 260], sleeve)
    add('sleeve_right', '角色左側露肩袖', 'armR', [375, 260], f'<g transform="translate(600 0) scale(-1 1)">{sleeve}</g>')
    add('costume_skirt', '非對稱白紫前裙', 'body', [300, 449],
        path('M252 414 Q298 428 349 414 L377 548 L340 528 L313 570 L294 545 L266 584 L230 550 L218 563Z', 'url(#silk)') +
        path('M252 420 L277 439 L252 546 L233 557 L241 503 M283 443 L298 454 L288 545 L269 565 M323 439 L341 430 L360 534 L340 519 L322 551', 'url(#violet)', '#c7b4d8', 1) +
        path('M239 426 L218 553 L231 543 L266 575 L294 535 L313 558 L340 516 L373 538', 'none', '#dfcfaf', 2))
    add('costume_bodice', '白色胸衣與黑色束腰', 'body', [300, 449],
        path('M248 277 Q269 264 300 291 Q332 264 352 277 L342 317 Q343 358 352 403 L333 444 L300 460 L260 442 L247 414 Q264 363 258 316Z', 'url(#dark)') +
        path('M240 268 Q254 260 274 276 L300 291 L325 276 Q345 259 360 269 L348 306 Q321 320 300 305 Q278 320 252 306Z', 'url(#silk)', '#a993af') +
        path('M247 277 Q270 285 296 299 M304 299 Q333 282 354 277 M264 321 Q275 373 260 425 M335 322 Q328 375 341 424', 'none', '#d9c6a1', 1.5) +
        path('M283 323 L316 339 L284 352 L317 367 L282 381 L319 396 L278 413 M316 324 L283 339 L316 352 L282 367 L318 381 L280 396 L322 414', 'none', '#b8a58b', 1) +
        path('M245 409 Q296 427 350 403 L350 416 Q300 443 250 425Z', 'url(#violet)', '#cfb995') + jewel(300,309,11) + jewel(299,429,12))
    add('neck_accessory', '黑色頸飾與肩帶', 'body', [300, 239],
        path('M280 219 Q300 229 320 219 L321 233 L300 250 L279 232Z', 'url(#dark)', '#a9959f') +
        path('M281 235 L254 274 M319 235 L346 274', 'none', '#403747', 5) + jewel(300,237,10))
    belt = path('M257 418 Q239 445 241 477 L250 463 L261 488 L270 428Z', 'url(#violet)', '#baa5c1') + flower(255,426,.42) + jewel(247,466,7)
    add('costume_jewels', '腰花與金色飾件', 'body', [300, 449], belt + f'<g transform="translate(600 0) scale(-1 1)">{belt}</g>')
    add('face', '臉部・完整底色', 'head', [300, 218],
        ellipse(242,165,9,16,'url(#skin)') + ellipse(358,165,9,16,'url(#skin)') +
        path('M244 119 Q250 78 301 80 Q352 80 359 121 L353 174 Q348 203 300 222 Q253 204 248 176Z', 'url(#skin)', '#b8a0ac', 1.5) +
        ellipse(262,180,20,10,'url(#blush)') + ellipse(338,180,20,10,'url(#blush)') + path('M300 165 L297 178 L301 180', 'none', '#d4a7b3', 1),
        '眼睛、眉毛與嘴巴底下皆保留完整臉色，不會因眨眼露出洞。')
    for side, x in [('left',270), ('right',330)]:
        # Closed lids and open eyes live in separate wrappers for crossfade/scale animation.
        eye = path(f'M{x-19} 155 Q{x} 143 {x+19} 155 Q{x+10} 174 {x-7} 170Z', '#fffafc', '#74617e', 1)
        eye += ellipse(x,158,10,12,'url(#iris)') + ellipse(x,155,3.5,8,'#41324f') + ellipse(x-3,152,3.5,3.5,'#fff') + ellipse(x+4,163,2,1.7,'#ffe8fd')
        eye += path(f'M{x-21} 151 Q{x-3} 139 {x+20} 153 M{x-18} 150 L{x-23} 146 M{x-13} 147 L{x-16} 143', 'none', '#514053', 2.8)
        add(f'eye_{side}', '眼睛・紫色虹膜', 'head', [x,156], f'<g id="eye_open_{side}">{eye}</g><g id="eye_closed_{side}" opacity="0">'+path(f'M{x-20} 156 Q{x} 169 {x+20} 156 M{x-16} 159 L{x-21} 162', 'none', '#675069', 2.7)+'</g>')
        add(f'brow_{side}', '眉毛', 'head', [x,139], path(f'M{x-17} 136 Q{x} 130 {x+15} 137', 'none', '#a28ca7', 2))
    add('mouth', '嘴巴・閉口與開口', 'head', [300,194],
        '<g id="mouth_closed">'+path('M291 194 Q300 199 309 193', 'none', '#b8798e', 1.7)+'</g>'+
        '<g id="mouth_open" opacity="0">'+ellipse(300,196,7,8,'#94526d')+ellipse(300,200,4.5,2.4,'#e9a0b4')+'</g>')
    add('hair_front', '前髮・分束瀏海', 'head', [300,110],
        path('M235 151 Q218 108 250 79 Q289 39 333 74 Q378 86 368 152 Q352 123 340 118 Q340 143 328 153 Q324 128 305 112 Q312 144 302 153 Q282 127 276 113 Q281 146 257 164 L260 129 Q248 153 244 176Z', 'url(#hair)') +
        path('M301 69 Q324 83 339 118 M281 76 Q262 96 260 129 M320 80 Q355 98 360 130 M295 78 Q284 92 278 112 M240 129 Q232 101 261 81', 'none', '#b8abc7', 1.3) +
        path('M271 84 Q284 73 298 73 M332 86 Q349 99 351 112', 'none', '#fffaff', 3))
    add('hair_side_left', '左側髮束', 'hairFrontL', [247,136],
        path('M245 124 Q230 177 242 216 Q251 254 223 297 Q234 257 220 221 Q207 181 227 134Z', 'url(#hair)') + path('M234 146 Q221 182 234 222 Q245 257 226 289', 'none', '#f5effc', 2.7))
    add('hair_side_right', '右側髮束', 'hairFrontR', [351,136],
        path('M350 123 Q370 171 357 218 Q344 252 373 300 Q364 257 381 217 Q393 175 369 134Z', 'url(#hair)') + path('M366 145 Q382 182 367 222 Q354 258 373 289', 'none', '#f9f1ff', 2.7))
    add('hair_ornament', '左側紫色緞帶與花飾', 'head', [246,113],
        path('M237 105 L206 69 L211 116 L177 131 L221 143 L198 208 L230 191 L240 211 L255 121Z', 'url(#violet)', '#bdaccd') +
        path('M216 122 L192 142 L221 137 M231 146 L214 183 L229 176', 'none', '#c5b59d', 1.3) + flower(239,114,.75) +
        path('M244 137 Q246 158 241 178', 'none', '#d6c09a', 1.6) + jewel(241,180,5) +
        flower(363,143,.32))
    return layers


def build(output, png=True):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    layer_dir = output / 'layers'
    layer_dir.mkdir(exist_ok=True)
    layers = make_layers()
    full = ''
    records = []
    if png:
        import cairosvg
    for order, layer in enumerate(layers):
        content = layer.pop('content')
        wrapped = f'<g id="{layer["id"]}" data-rig="{layer["rig"]}">{content}</g>'
        full += wrapped
        filename = f'{order:02d}_{layer["id"]}'
        data = svg(wrapped)
        (layer_dir / f'{filename}.svg').write_text(data, encoding='utf-8')
        if png:
            cairosvg.svg2png(bytestring=data.encode(), write_to=str(layer_dir / f'{filename}.png'))
        records.append({**layer, 'order': order, 'svg': f'layers/{filename}.svg',
                        'png': f'layers/{filename}.png' if png else None,
                        'sha256': hashlib.sha256(data.encode()).hexdigest()})
    master = svg(full)
    (output / 'character.svg').write_text(master, encoding='utf-8')
    if png:
        cairosvg.svg2png(bytestring=master.encode(), write_to=str(output / 'character.png'))
    manifest = {'schema_version':1, 'name':'銀鈴 / Silverbell', 'age':'adult, 20+',
        'artifact_type':'procedural_layered_2d_character', 'official_cubism_model':False,
        'canvas':{'width':W,'height':H,'origin':'top-left','units':'pixels'},
        'artwork':'Simplified original vector redraw guided by the user-supplied reference board. Not an AI illustration or automatic extraction.',
        'reference_features':['silver-white long hair','violet eyes','left flower and ribbon',
            'white off-shoulder sleeves','black fitted bodice','lavender asymmetric skirt','asymmetric stockings','gold trim'],
        'occlusion_method':'Complete face, neck, shoulders, torso, arm caps and back hair drawn underneath covering layers; no generative inpainting.',
        'layers':records,
        'parameters':{'eyeOpen':[0,1], 'mouthOpen':[0,1], 'breath':[0,1], 'headAngle':[-5,5], 'hairSway':[-4,4]},
        'master_sha256':hashlib.sha256(master.encode()).hexdigest()}
    (output / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='web/assets/character')
    parser.add_argument('--svg-only',action='store_true')
    args=parser.parse_args()
    result=build(args.output,not args.svg_only)
    print(f'Built {len(result["layers"])} layers in {args.output}')
