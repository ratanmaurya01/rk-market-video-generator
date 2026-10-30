"""

Handwriting Explainer Video Maker  (Python 3 + Pillow + numpy + imageio-ffmpeg)

Setup : pip install pillow numpy imageio-ffmpeg

Run   : python video.py   ->  output.mp4  (1080x1920, 9:16)

"""

import os, subprocess, math, wave, shutil, urllib.request

import numpy as np, imageio_ffmpeg

from PIL import Image, ImageDraw, ImageFont, features



W, H, FPS = 1080, 1920, 30

HERE = os.path.dirname(os.path.abspath(__file__))



def fetch(url, dest, min_size=50_000):

    if os.path.exists(dest) and os.path.getsize(dest) >= min_size:

        return True

    try:

        tmp = dest + '.part'

        urllib.request.urlretrieve(url, tmp)

        if os.path.getsize(tmp) < min_size:

            os.remove(tmp); return False

        os.replace(tmp, dest); return True

    except Exception as e:

        print('Download failed:', url, e); return False



FONT = os.path.join(HERE, 'Kalam-Bold.ttf')

if not fetch('https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Bold.ttf', FONT):

    raise SystemExit('Kalam-Bold.ttf download nahi hua. Internet check karo ya font file same folder me rakho.')



if not features.check('raqm'):

    print('WARNING: Pillow me RAQM nahi hai, Hindi matras/conjuncts galat dikh sakte hain (Colab/WSL me chalao).')



OUT = 'output.mp4'

LOGO_MAIN = 'RK'; LOGO_SUB = 'Market Talk'

BLUE=(24,64,160); RED=(205,50,40); GRN=(18,135,62); ORG=(232,115,20); DK=(45,45,60); PUR=(125,55,165)



def cl(x): return max(0.0, min(1.0, x))

def eoc(x): x = cl(x); return 1-(1-x)**3

def back(x):

    x = cl(x) - 1; return 1 + 2.70158*x**3 + 1.70158*x**2



_f = {}

def F(s):

    s = int(s); _f.setdefault(s, ImageFont.truetype(FONT, s)); return _f[s]



# ---------- paper ----------*

rr = np.random.default_rng(2); a = np.zeros((H, W, 3), np.float32); a[:] = (251, 246, 230)

a += rr.normal(0, 2.2, (H, W, 1))

yy, xx = np.mgrid[0:H, 0:W]; v = np.hypot((xx-W/2)/W, (yy-H/2)/H); a -= (v**2*38)[:, :, None]

PAPER = Image.fromarray(a.clip(0, 255).astype(np.uint8)); pd = ImageDraw.Draw(PAPER)

for y in range(200, H, 76): pd.line((0, y, W, y), fill=(205,222,240), width=2)

pd.line((130, 0, 130, H), fill=(228,130,130), width=3)

for y in range(150, H, 300): pd.ellipse((34, y, 66, y+32), fill=(200,196,185), outline=(170,165,155), width=2)



# ---------- elements ----------*

class Page:

    def __init__(s, dur): s.dur = dur; s.els = []



def jit(pl, seed, amp=1.3, step=14):

    r = np.random.default_rng(seed); out = []

    for p, q in zip(pl[:-1], pl[1:]):

        n = max(1, int(math.dist(p, q)/step))

        for k in range(n):

            f = k/n; out.append((p[0]+(q[0]-p[0])*f+r.normal(0, amp), p[1]+(q[1]-p[1])*f+r.normal(0, amp)))

    out.append(pl[-1]); return out



SEED = [100]

def path(pg, pls, color, w, t0, dur, fill=None, fa=235):

    SEED[0] += 1; P = []; allp = []

    for i, pl in enumerate(pls):

        j = jit(pl, SEED[0]*7+i); cum = [0]

        for p, q in zip(j[:-1], j[1:]): cum.append(cum[-1]+math.dist(p, q))

        P.append((j, cum)); allp += j

    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]; pad = w+8

    el = dict(k='path', P=P, color=color, w=w, t0=t0, dur=dur, fill=fill, fa=fa, total=sum(c[-1] for _, c in P),

              bb=(int(min(xs)-pad), int(min(ys)-pad), int(max(xs)+pad), int(max(ys)+pad)), cache=None)

    pg.els.append(el); return t0+dur



def text(pg, msg, x, y, size, color, t0, dur=None, align='c'):

    ends = t0

    for i, line in enumerate(msg.split('\n')):

        s = size

        while F(s).getlength(line)+50 > W-100 and s > 12: s -= 3

        f = F(s); w = int(f.getlength(line))+50; h = sum(f.getmetrics())+34

        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((25, 17), line, font=f, fill=color+(255,))

        SEED[0] += 1; ang = np.random.default_rng(SEED[0]).uniform(-1.3, 1.3)

        lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC); w, h = lay.size

        d = dur if dur else max(0.5, len(line)*0.075)

        yy_ = y+i*int(size*1.3); xl = (x-w/2) if align == 'c' else (x-25)

        pg.els.append(dict(k='text', lay=lay, x=xl, y=yy_-h/2, w=w, h=h, t0=ends, dur=d)); ends += d

    return ends



# ---------- emoji support ----------*

EMOJI_CANDIDATES = [

    (r'C:\Windows\Fonts\seguiemj.ttf', 109),

    ('/System/Library/Fonts/Apple Color Emoji.ttc', 160),

    ('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109),

    (os.path.join(HERE, 'NotoColorEmoji.ttf'), 109),

]

EMOJI_F = None

for _p, _s in EMOJI_CANDIDATES:

    if os.path.exists(_p):

        try:

            _f_try = ImageFont.truetype(_p, _s)

            _t = Image.new('RGBA', (300, 300), (0, 0, 0, 0))

            ImageDraw.Draw(_t).text((0, 0), '🔥', font=_f_try, embedded_color=True)

            if _t.getbbox():

                EMOJI_F = _f_try; print('Emoji font:', _p); break

        except Exception as e:

            print('Emoji font fail:', _p, e)

if EMOJI_F is None:

    print('Koi emoji font nahi mila, video bina emoji ke banega.')



def emoji(pg, ch, x, y, size, t0, dur=0.35):

    if EMOJI_F is None: return t0+dur

    try:

        lay = Image.new('RGBA', (300, 300), (0, 0, 0, 0))

        ImageDraw.Draw(lay).text((0, 0), ch, font=EMOJI_F, embedded_color=True)

        bb = lay.getbbox()

        if not bb: return t0+dur

        lay = lay.crop(bb)

        k = size/max(lay.size); lay = lay.resize((max(1, int(lay.width*k)), max(1, int(lay.height*k))), Image.LANCZOS)

        SEED[0] += 1; ang = np.random.default_rng(SEED[0]).uniform(-10, 10)

        lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC)

    except Exception:

        return t0+dur

    pg.els.append(dict(k='emo', lay=lay, cx=x, cy=y, t0=t0, dur=dur))

    return t0+dur



def render_path(el, p):

    if p >= 1 and el['cache']: return el['cache']

    bx0, by0, bx1, by1 = el['bb']; S = 2; bw, bh = bx1-bx0, by1-by0

    lay = Image.new('RGBA', (bw*S, bh*S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); col = el['color']+(255,)

    if el['fill'] and p > 0.5:

        pts = [((x-bx0)*S, (y-by0)*S) for x, y in el['P'][0][0]]

        d.polygon(pts, fill=el['fill']+(int(el['fa']*cl((p-0.5)/0.4)),))

    target = p*el['total']; acc = 0; pen = None

    for pts, cum in el['P']:

        L = cum[-1]

        if acc+L <= target: seg = pts

        else:

            rem = target-acc; k = max(1, next(i for i, c in enumerate(cum) if c >= rem)); f = (rem-cum[k-1])/max(1e-6, cum[k]-cum[k-1])

            seg = pts[:k]+[(pts[k-1][0]+(pts[k][0]-pts[k-1][0])*f, pts[k-1][1]+(pts[k][1]-pts[k-1][1])*f)]

        if len(seg) > 1:

            sp = [((x-bx0)*S, (y-by0)*S) for x, y in seg]; d.line(sp, fill=col, width=el['w']*S, joint='curve')

            for q in (sp[0], sp[-1]): d.ellipse((q[0]-el['w'], q[1]-el['w'], q[0]+el['w'], q[1]+el['w']), fill=col)

        if acc+L > target: pen = seg[-1]; break

        acc += L

    out = lay.resize((bw, bh), Image.LANCZOS)

    if p >= 1: el['cache'] = (out, None)

    return out, pen



def draw_pg(pg, t):

    img = PAPER.copy(); pen = None; last = -1

    for el in pg.els:

        p = cl((t-el['t0'])/el['dur']) if t >= el['t0'] else 0

        if p <= 0: continue

        if el['k'] == 'emo':

            s = max(0.05, back(p)); lay = el['lay']

            if p < 1:

                w2 = max(1, int(lay.width*s)); h2 = max(1, int(lay.height*s)); im = lay.resize((w2, h2), Image.BILINEAR)

            else:

                im = lay; w2, h2 = lay.size

            img.paste(im, (int(el['cx']-w2/2), int(el['cy']-h2/2)), im)

        elif el['k'] == 'text':

            cw = max(1, int(el['w']*p)); crop = el['lay'].crop((0, 0, cw, el['h']))

            img.paste(crop, (int(el['x']), int(el['y'])), crop)

            if p < 1 and el['t0'] > last: last = el['t0']; pen = (el['x']+el['w']*p-20, el['y']+el['h']*0.72)

        else:

            out, pp = render_path(el, p); img.paste(out, (el['bb'][0], el['bb'][1]), out)

            if p < 1 and pp and el['t0'] > last: last = el['t0']; pen = pp

    if pen:

        x, y = pen[0], pen[1]+4*math.sin(t*30); d = ImageDraw.Draw(img); u = (0.42, -0.9); v_ = (0.9, 0.42)

        P = lambda a_, b_: (x+u[0]*a_+v_[0]*b_, y+u[1]*a_+v_[1]*b_)

        d.polygon([P(0,0), P(38,-11), P(38,11)], fill=(238,200,150)); d.polygon([P(0,0), P(14,-4), P(14,4)], fill=(60,60,70))

        d.polygon([P(38,-11), P(38,11), P(180,11), P(180,-11)], fill=(250,200,40), outline=(150,110,10))

        d.polygon([P(180,-11), P(180,11), P(205,11), P(205,-11)], fill=(240,140,150))

    return img



# ---------- geometry ----------*

def circ(cx, cy, r, n=36): return [(cx+r*math.cos(2*math.pi*i/n-math.pi/2), cy+r*math.sin(2*math.pi*i/n-math.pi/2)) for i in range(n+3)]

def rect(x0, y0, x1, y1): return [(x0,y0), (x1,y0), (x1,y1), (x0,y1), (x0,y0)]

def wavy(x0, x1, y, amp=9, n=14): return [(x0+(x1-x0)*i/n, y+amp*math.sin(i*1.6)) for i in range(n+1)]

def arrow(x0, y0, x1, y1, h=34):

    a_ = math.atan2(y1-y0, x1-x0); return [[(x0,y0), (x1,y1)], [(x1-h*math.cos(a_-.5), y1-h*math.sin(a_-.5)), (x1,y1), (x1-h*math.cos(a_+.5), y1-h*math.sin(a_+.5))]]



# =====================================================================*

# RK MARKET TALK — LIQUIDITY KYA HOTA HAI?  (\~70 sec, 3 charts)*

# Educational illustration only — not Buy/Sell advice.*

# =====================================================================*



pages = []



# P1 — HOOK*

p = Page(5.6); pages.append(p)

text(p, "Profit दिख रहा है,", 540, 400, 84, ORG, 0.1, 0.7)

text(p, "पर बेच नहीं पा रहे?", 540, 570, 84, RED, 0.8, 0.7)

emoji(p, "😱", 540, 790, 180, 1.5)

text(p, "इसकी वजह है...", 540, 1010, 70, DK, 1.9, 0.7)

text(p, "LIQUIDITY", 540, 1200, 130, BLUE, 2.7, 0.9)

path(p, [wavy(200, 880, 1300, 9)], RED, 9, 3.7, 0.4)

emoji(p, "💧", 540, 1470, 160, 4.1)



# P2 — DEFINITION*

p = Page(8.0); pages.append(p)

text(p, "Liquidity क्या है?", 540, 380, 98, PUR, 0.1, 0.8)

text(p, "Asset को कितनी जल्दी,", 540, 580, 66, DK, 1.0, 0.8)

text(p, "सही दाम पर Cash में", 540, 710, 66, DK, 1.8, 0.8)

text(p, "बदल सको!", 540, 850, 84, GRN, 2.6, 0.7)

path(p, [rect(200, 1000, 450, 1160)], BLUE, 8, 3.4, 0.4)

text(p, "Stock", 325, 1080, 56, BLUE, 3.7, 0.5)

path(p, arrow(470, 1080, 610, 1080), DK, 9, 4.2, 0.4)

path(p, [rect(630, 1000, 880, 1160)], GRN, 8, 4.6, 0.4)

text(p, "Cash", 755, 1080, 56, GRN, 5.0, 0.5)

emoji(p, "📈", 325, 1280, 120, 5.6)

emoji(p, "💵", 755, 1280, 120, 5.8)

text(p, "जितना आसान, उतना Liquid", 540, 1460, 62, ORG, 6.1, 0.8)



# P3 — CHART 1: LIQUIDITY LADDER*

p = Page(8.0); pages.append(p)

text(p, "Liquidity की सीढ़ी", 540, 380, 90, PUR, 0.1, 0.8)

rows = [("Cash — तुरंत", 700, GRN),

        ("बड़े Stocks — कुछ सेकंड", 560, BLUE),

        ("Small Stocks — कभी-कभी अटकता", 260, ORG),

        ("Property — महीनों लग सकते हैं", 100, RED)]

for i, (lab, L, c) in enumerate(rows):

    y = 620 + i*180; t = 1.0 + i*1.3

    text(p, lab, 170, y-45, 46, c, t, 0.6, 'l')

    path(p, [rect(170, y, 170+L, y+60)], c, 6, t+0.5, 0.5, fill=c, fa=210)

text(p, "लंबा Bar = ज़्यादा Liquid", 540, 1380, 62, DK, 6.2, 0.8)

emoji(p, "📊", 540, 1520, 130, 7.0)



# P4 — CHART 2: ORDER BOOK*

p = Page(7.5); pages.append(p)

text(p, "Order Book", 540, 370, 92, BLUE, 0.1, 0.8)

text(p, "(Buyers और Sellers की लाइन)", 540, 450, 44, DK, 0.9, 0.6)

text(p, "Buyers", 300, 540, 56, GRN, 1.0, 0.5)

text(p, "Sellers", 780, 540, 56, RED, 1.4, 0.5)

path(p, [[(540, 590), (540, 1190)]], DK, 6, 1.0, 0.5)

buy_len = [380, 320, 250, 170, 100]

sell_len = [100, 170, 250, 320, 380]

for i in range(5):

    y = 620 + i*110; t = 1.9 + i*0.35

    path(p, [rect(520-buy_len[i], y, 520, y+70)], GRN, 5, t, 0.3, fill=GRN, fa=200)

    path(p, [rect(560, y, 560+sell_len[i], y+70)], RED, 5, t+0.15, 0.3, fill=RED, fa=200)

text(p, "ज़्यादा Buyers + Sellers", 540, 1300, 66, ORG, 4.3, 0.8)

text(p, "= आसानी से Trade", 540, 1420, 66, GRN, 5.2, 0.8)

emoji(p, "🤝", 540, 1530, 100, 6.0)



# P5 — BID-ASK SPREAD*

p = Page(9.2); pages.append(p)

text(p, "Bid-Ask Spread", 540, 370, 90, PUR, 0.1, 0.8)

text(p, "Liquid Stock", 300, 520, 52, GRN, 1.0, 0.5)

text(p, "Illiquid Stock", 780, 520, 52, RED, 1.3, 0.5)

path(p, [rect(150, 600, 450, 900)], GRN, 8, 1.6, 0.4)

path(p, [rect(630, 600, 930, 900)], RED, 8, 1.9, 0.4)

text(p, "Ask ₹100.10", 300, 680, 38, DK, 2.3, 0.45)

text(p, "Bid ₹100.00", 300, 760, 38, DK, 2.8, 0.45)

text(p, "फ़र्क = ₹0.10", 300, 840, 44, GRN, 3.3, 0.5)

text(p, "Ask ₹108", 780, 680, 38, DK, 3.8, 0.45)

text(p, "Bid ₹100", 780, 760, 38, DK, 4.25, 0.45)

text(p, "फ़र्क = ₹8", 780, 840, 44, RED, 4.7, 0.5)

text(p, "खरीदते Ask पर, बेचते Bid पर", 540, 985, 46, DK, 5.3, 0.7)

text(p, "Spread छोटा = Liquid", 540, 1110, 66, GRN, 6.0, 0.7)

text(p, "Spread बड़ा = Illiquid", 540, 1240, 66, RED, 6.65, 0.7)

text(p, "Spread आपका छुपा Cost है!", 540, 1370, 62, ORG, 7.3, 0.8)

emoji(p, "💸", 540, 1510, 130, 8.1)



# P6 — CHART 3: PRICE IMPACT*

p = Page(9.2); pages.append(p)

text(p, "बड़ा Order बेचा तो दाम?", 540, 370, 76, BLUE, 0.1, 0.8)

text(p, "इसे Slippage कहते हैं", 540, 520, 52, ORG, 0.9, 0.8)

path(p, [[(200, 1250), (200, 650)]], DK, 6, 1.8, 0.4)

path(p, [[(200, 1250), (900, 1250)]], DK, 6, 2.1, 0.4)

text(p, "दाम", 250, 610, 42, DK, 2.4, 0.3)

text(p, "बेची गई Quantity", 540, 1320, 44, DK, 2.6, 0.6)

path(p, [[(220, 760), (400, 775), (600, 790), (880, 800)]], GRN, 10, 3.3, 1.0)

path(p, [[(220, 760), (400, 850), (560, 1000), (720, 1130), (880, 1200)]], RED, 10, 4.4, 1.4)

emoji(p, "📉", 700, 950, 110, 5.9)

text(p, "हरी लाइन: Liquid — दाम टिका रहता है", 540, 1420, 46, GRN, 6.2, 0.9)

text(p, "लाल लाइन: Illiquid — दाम गिरता जाता है", 540, 1500, 46, RED, 7.2, 0.9)



# P7 — RISKS*

p = Page(8.2); pages.append(p)

text(p, "Illiquid में Risk!", 540, 370, 92, RED, 0.1, 0.8)

items = [("Exit मुश्किल", "बेचना चाहो, पर Buyer नहीं"),

         ("Spread = छुपा Cost", "खरीद-बिक्री में ही नुकसान"),

         ("Lower Circuit का डर", "सब Seller, Buyer कोई नहीं"),

         ("Price आसानी से हिलता है", "कम Volume = ज़्यादा उतार-चढ़ाव")]

for i, (a_, b_) in enumerate(items):

    y = 560 + i*190; t = 1.0 + i*1.2

    path(p, [circ(190, y+35, 45)], RED, 7, t, 0.3)

    text(p, str(i+1), 190, y+35, 50, RED, t+0.2, 0.25)

    text(p, a_, 270, y, 56, DK, t+0.3, 0.5, 'l')

    text(p, b_, 270, y+65, 40, BLUE, t+0.8, 0.5, 'l')

text(p, "Volume देखो, फिर Trade करो!", 540, 1340, 60, ORG, 6.0, 0.8)

emoji(p, "⚠️", 540, 1480, 140, 6.8)



# P8 — HOW TO CHECK*

p = Page(8.2); pages.append(p)

text(p, "Liquidity कैसे Check करें?", 540, 380, 74, PUR, 0.1, 0.9)

checks = ["Daily Volume ज़्यादा हो", "Bid-Ask Spread छोटा हो",

          "Market Depth में Orders हों", "Market Cap बड़ा हो (आम तौर पर)"]

for i, c in enumerate(checks):

    y = 600 + i*180; t = 1.1 + i*1.1

    path(p, [[(150, y+5), (175, y+35), (225, y-30)]], GRN, 10, t, 0.3)

    text(p, c, 250, y, 46, DK, t+0.2, 0.7, 'l')

text(p, "ये सब Broker App में दिखता है!", 540, 1330, 56, PUR, 5.4, 0.8)

emoji(p, "📱", 540, 1480, 140, 6.3)

text(p, "Education Only | Not Buy/Sell Advice", 540, 1640, 34, RED, 6.6, 0.5)



# P9 — CLOSE + CTA*

p = Page(6.0); pages.append(p)

text(p, "याद रखो Trader!", 540, 380, 94, ORG, 0.1, 0.7)

text(p, "Liquidity = Exit का रास्ता", 540, 590, 74, BLUE, 0.9, 0.9)

emoji(p, "🚪", 540, 800, 170, 1.9)

text(p, "Profit तभी Real है,", 540, 1010, 70, DK, 2.3, 0.7)

text(p, "जब बेचना भी आसान हो!", 540, 1170, 74, GRN, 3.0, 0.8)

emoji(p, "💧", 540, 1350, 140, 3.9)

text(p, "Follow RK MARKET TALK", 540, 1520, 54, BLUE, 4.3, 0.7)

text(p, "Education Only | Not Buy/Sell Advice", 540, 1640, 34, RED, 4.9, 0.5)



# =================== END OF YOUR TOPIC ===================*



starts = [0]

for pg in pages: starts.append(starts[-1]+pg.dur)

TOTAL = starts[-1]



def logo(img):

    d = ImageDraw.Draw(img)

    for i, (h, c) in enumerate([(24,(255,153,51)), (38,(120,120,130)), (54,(19,150,60))]): d.rectangle((760+i*20, 128-h, 774+i*20, 128), fill=c)

    d.line((756,104, 786,92, 802,98, 826,70), fill=(240,190,0), width=4)

    d.text((1040,86), LOGO_MAIN, font=F(66), fill=DK, anchor='rm'); d.text((1040,132), LOGO_SUB, font=F(34), fill=RED, anchor='rm')



def frame(T):

    i = max(k for k in range(len(pages)) if starts[k] <= T+1e-9); tl = T-starts[i]

    img = draw_pg(pages[i], tl)

    if i > 0 and tl < 0.45:

        e = eoc(tl/0.45); old = draw_pg(pages[i-1], pages[i-1].dur+tl); can = Image.new('RGB', (W, H))

        can.paste(old, (-int(W*e), 0)); can.paste(img, (int(W*(1-e)), 0))

        ImageDraw.Draw(can).line((int(W*(1-e)), 0, int(W*(1-e)), H), fill=(150,140,120), width=6); img = can

    logo(img); return img



def audio():

    SR = 44100; n = int(TOTAL*SR)+SR; t = np.arange(n)/SR; r = np.random.default_rng(4); mix = np.zeros(n)

    for f, am in [(130.8,.05), (196,.04), (261.6,.035), (329.6,.03), (392,.02)]: mix += np.sin(2*np.pi*f*t)*am*(0.6+0.4*np.sin(2*np.pi*0.12*t+f))

    for k in range(int(TOTAL/0.5)):

        s = int(k*0.5*SR); f = [523.3, 659.3, 784, 659.3][k % 4]; L = min(int(0.45*SR), n-s); x = np.arange(L)/SR

        mix[s:s+L] += np.sin(2*np.pi*f*x)*np.exp(-x/0.12)*0.018

    for pi, pg in enumerate(pages):

        for el in pg.els:

            s = int((starts[pi]+el['t0'])*SR)

            if el['k'] == 'emo':

                L = min(int(0.18*SR), n-s); x = np.arange(L)/SR

                mix[s:s+L] += np.sin(2*np.pi*(700+900*x/0.18)*x)*np.exp(-x/0.05)*0.06; continue

            L = min(int(el['dur']*SR), n-s); nz = np.diff(r.standard_normal(L+1))*(0.5+0.5*np.sin(2*np.pi*14*np.arange(L)/SR))

            mix[s:s+L] += nz*0.045*np.minimum(1, np.minimum(np.arange(L)/800, (L-np.arange(L))/800))

        if pi > 0:

            s = int(starts[pi]*SR); L = int(0.4*SR); x = np.arange(L)/L; mix[s:s+L] += r.standard_normal(L)*np.sin(np.pi*x)*0.12

    s = int((TOTAL-1.5)*SR); L = int(1.2*SR); x = np.arange(L)/SR; mix[s:s+L] += np.sin(2*np.pi*1046.5*x)*np.exp(-x/0.4)*0.12

    mix = mix[:int(TOTAL*SR)]; m = len(mix); mix *= np.minimum(1, (m-np.arange(m))/(0.8*SR)); mix = mix/np.abs(mix).max()*0.7

    w = wave.open('a.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes()); w.close()



if __name__ == '__main__':

    audio(); N = int(TOTAL*FPS)

    ffmpeg = shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()

    tmp_out = OUT+'.tmp.mp4'

    pr = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',

                           '-i', 'a.wav', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast', '-crf', '19',

                           '-c:a', 'aac', '-b:a', '160k', '-shortest', '-f', 'mp4', tmp_out], stdin=subprocess.PIPE)

    for k in range(N): pr.stdin.write(frame(k/FPS).tobytes())

    pr.stdin.close()

    if pr.wait() != 0: raise RuntimeError(f'FFmpeg failed; incomplete video is at {tmp_out}')

    os.replace(tmp_out, OUT)

    print(f'Created {os.path.abspath(OUT)} ({TOTAL:.1f} seconds)')
