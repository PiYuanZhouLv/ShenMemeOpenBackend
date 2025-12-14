# Fix the missing function get_emoji_unicode_dict which pilmoji needs.
import emoji
emoji.unicode_codes.get_emoji_unicode_dict = lambda lang: {
    data[lang]: emj
    for emj, data in emoji.EMOJI_DATA.items()
    if lang in data and data['status'] <= emoji.STATUS['fully_qualified']
}
# End fix.

from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import requests as rq
from io import BytesIO

app = Flask(__name__)

def auto_newline(emoji: Pilmoji, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, init_fontsize: int, max_width: int) -> str:
    width, _ = emoji.getsize(text, font.font_variant(size=init_fontsize))
    print(width/max_width)
    div = int((width/max_width)**(0.5+5/len(text)))
    if div==0:
        emoji.text((xy[0]+(max_width-width)//2, xy[1]), text, 'black', font.font_variant(size=init_fontsize), align='center', emoji_position_offset=(0, round(30/145*init_fontsize)))
        return
    ffont = font.font_variant(size=init_fontsize//int(div))
    step = len(text) // div + 1
    lines = [text[i:i+step] for i in range(0, len(text), step)]
    final = '\n'.join(lines)
    final_size = emoji.getsize(final, ffont)
    img_text = Image.new("RGB", (int(final_size[0]), int(final_size[1]+30)), (255, 255, 255))
    with Pilmoji(img_text) as text_emoji:
        y = 0
        for line in lines:
            dx, dy = text_emoji.getsize(line, ffont)
            text_emoji.text(((img_text.size[0]-dx)//2, y), line, 'black', ffont, align='center', emoji_position_offset=(0, round(30/145*(init_fontsize//int(div)))))
            y += dy
    rate = min(max_width/img_text.size[0], init_fontsize/img_text.size[1])
    new_size = tuple(map(lambda x: x*rate, img_text.size))
    emoji.image.paste(img_text.resize(map(int, new_size)), (int(xy[0]+(max_width-new_size[0])//2), int(xy[1]+(init_fontsize-new_size[1])//2)))

@app.route('/meme')
def generate_meme():
    if 'qq' not in request.args:
        return 'Param "qq" is required.', 400
    
    qqId = request.args['qq']
    name = request.args.get('name', qqId)
    comment = request.args.get('comment', '牛逼')
    call = request.args.get('call', '神')
    appel = request.args.get('appellation', '他')

    try:
        io = BytesIO(rq.get(f'http://q.qlogo.cn/headimg_dl?dst_uin={qqId}&spec=640&img_type=jpg').content)
        img = Image.open(io)
    except:
        return 'Something wrong with QQ\'s Avatar API.', 500
    
    meme = Image.new("RGB", (1024, 1024), (255, 255, 255))
    fontDB = ImageFont.truetype(r'C:\Windows\Fonts\MSYHBD.TTC')
    font = ImageFont.truetype(r'C:\Windows\Fonts\MSYH.TTC')
    draw = ImageDraw.Draw(meme)
    with Pilmoji(meme) as emoji:
        auto_newline(emoji, (10, 10), f'请问你见到 {name} 了吗', fontDB, 145, 1004)
        meme.paste(img.resize((690, 690)), (167, 160))
        auto_newline(emoji, (10, 854), f'非常{comment}！简直就是{call}!', fontDB, 110, 1004)
        auto_newline(emoji, (0, 964), f'{appel}也没失踪也没怎么样，我只是觉得你们都该看一下', font, 60, 1024)
    io = BytesIO()
    meme.save(io, 'jpeg')
    io.seek(0)
    return send_file(io, 'image/jpeg')

if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
