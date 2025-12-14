# Fix the missing function get_emoji_unicode_dict which pilmoji needs.
import emoji
emoji.unicode_codes.get_emoji_unicode_dict = lambda lang: {
    data[lang]: emj
    for emj, data in emoji.EMOJI_DATA.items()
    if lang in data and data['status'] <= emoji.STATUS['fully_qualified']
}
# End fix.

from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont, ImageChops
from pilmoji import Pilmoji
import requests as rq
from io import BytesIO

app = Flask(__name__)

def auto_newline(emoji: Pilmoji, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, init_fontsize: int, max_width: int) -> str:
    width, _ = emoji.getsize(text, font.font_variant(size=init_fontsize))
    print(width/max_width)
    div = int((width/max_width)**(0.5+5/len(text)))
    if div==0:
        fsize = init_fontsize
        ffont = font.font_variant(size=init_fontsize)
        lines = [text]
    else:
        fsize = init_fontsize//int(div)
        ffont = font.font_variant(size=fsize)
        step = len(text) // div + 1
        lines = [text[i:i+step] for i in range(0, len(text), step)]
    final = '\n'.join(lines)
    final_size = emoji.getsize(final, ffont)
    img_text = Image.new("RGB", (int(final_size[0]), int(final_size[1]+30)), (255, 255, 255))
    with Pilmoji(img_text) as text_emoji:
        y = 0
        for line in lines:
            dx, dy = text_emoji.getsize(line, ffont)
            text_emoji.text(((img_text.size[0]-dx)//2, y), line, 'black', ffont, align='center', emoji_position_offset=(0, round(30/145*(fsize))))
            y += dy
    chop = ImageChops.difference(img_text, Image.new("RGB", img_text.size, (255, 255, 255)))
    img_text = img_text.crop(chop.getbbox())
    rate = min(max_width/img_text.size[0], init_fontsize/img_text.size[1])
    new_size = tuple(map(lambda x: x*rate, img_text.size))
    emoji.image.paste(img_text.resize(map(int, new_size)), (int(xy[0]+(max_width-new_size[0])//2), int(xy[1]+(init_fontsize-new_size[1])//2)))

@app.route('/meme', methods=['GET', 'POST'])
def generate_meme():
    if 'qq' not in request.values:
        return 'Param "qq" is required.', 400
    
    qqId = request.values['qq']
    name = request.values.get('name', None) or qqId
    comment = request.values.get('comment', None) or '牛逼'
    call = request.values.get('call', None) or '神'
    appel = request.values.get('appellation', None) or '他'

    try:
        io = BytesIO(rq.get(f'http://q.qlogo.cn/headimg_dl?dst_uin={qqId}&spec=640&img_type=jpg').content)
        img = Image.open(io)
    except:
        return 'Something wrong with QQ\'s Avatar API.', 500
    
    meme = Image.new("RGB", (1024, 1024), (255, 255, 255))
    fontBD = ImageFont.truetype(r'C:\Windows\Fonts\MSYHBD.TTC')
    font = ImageFont.truetype(r'C:\Windows\Fonts\MSYH.TTC')
    # draw = ImageDraw.Draw(meme)
    with Pilmoji(meme) as emoji:
        auto_newline(emoji, (10, 10), f'请问你见到 {name} 了吗', fontBD, 145, 1004)
        meme.paste(img.resize((690, 690)), (167, 160))
        auto_newline(emoji, (10, 854), f'非常{comment}！简直就是{call}!', fontBD, 110, 1004)
        auto_newline(emoji, (0, 964), f'{appel}也没失踪也没怎么样，我只是觉得你们都该看一下', font, 60, 1024)
    io = BytesIO()
    meme.save(io, 'jpeg')
    io.seek(0)
    return send_file(io, 'image/jpeg')

@app.route('/')
def index():
    return \
'''
<!DOCTYPE html>
<head>
    <title> 神の表情包 </title>
</head>
<body>
    <form action="/meme" method="POST">
        <label>QQ号（qq=）<input name="qq" placeholder="必填" required>*必填</label><br>
        <label>显示名称（name=）<input name="name">默认为QQ号</label><br>
        <label>评论（comment=）<input placeholder="牛逼" name="comment">默认为“牛逼”</label><br>
        <label>称呼（call=）<input placeholder="神" name="call">默认为“神”</label><br>
        <label>称谓（appellation=）<input placeholder="他" name="appellation">默认为“他”</label><br>
        GET URL: <a id="url"></a><br>
        Submit by POST: <input type="submit">
    </form>
    <script>
        document.querySelector("input[name=name]").placeholder = document.querySelector("input[name=qq]").value || "默认为QQ号";
        document.querySelector("input[name=qq]").addEventListener("input", ()=>{
            document.querySelector("input[name=name]").placeholder = document.querySelector("input[name=qq]").value || "默认为QQ号";
        })
        function update(){
            if(!document.querySelector("input[name=qq]").value){
                document.getElementById("url").href = '#';
                document.getElementById("url").innerText = "QQ号为必填项";
                return;
            }
            document.getElementById("url").innerText = "/meme";
            let first = true;
            for(let i of document.forms[0].elements){
                if(i.type=="submit"){
                    continue;
                }
                if(i.value){
                    document.getElementById("url").innerText += `${first?"?":"&"}${i.name}=${i.value}`;
                    first = false;
                }
            }
            document.getElementById("url").href = document.getElementById("url").innerText;
        }
        update();
        for(let i of document.forms[0].elements){
            if(i.type=="submit"){
                continue;
            }
            i.addEventListener("input", update);
        }
    </script>
</body>
'''

if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
