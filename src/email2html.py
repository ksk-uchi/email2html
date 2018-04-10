#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import base64
import click
import email
import os
from lxml import html


@click.group()
def creator_grp():
    '''e-mail を HTML に変換するコマンド集'''
    pass


def imgConv(part):
    '''image/* のパートを受け取って、HTML image タグの src 属性に付与出来る形に整形する
    
    ただし、base64 形式出ない場合は無視する
    '''
    enc = part.get('Content-Transfer-Encoding')
    if enc != 'base64':
        return ('', '')
    content_id = part.get('Content-ID')
    content_type = part.get_content_type()
    payload = base64.b64encode(
        part.get_payload(decode=True)
    ).decode('utf-8')

    content_id = content_id[1:-1]
    base64payload = 'data:%s;%s,%s' % (content_type, enc, payload)
    return (content_id, base64payload)


def textPlainConv(part):
    '''text/plain のパートを受け取って HTML にして返す

    改行コード等は <br /> に置き換えて、全体を <pre> タグで囲って返す
    '''
    payload = part.get_payload(decode=True).decode('utf-8')
    # 改行コードとゼロ幅リターンは <br /> に置き換え
    html_text = payload.replace('\r\n', '<br />').replace('\u200b', '<br />')
    html_text = '<pre>%s</pre>' % html_text
    return html_text


def textHtmlConv(part):
    '''text/html のパートを受け取って HTML として返す'''
    payload = part.get_payload(decode=True).decode('utf-8')
    dom = html.fromstring(payload)
    html_text = html.tostring(dom, encoding='utf-8').decode('utf-8')
    return html_text


def buryImagesIntoMessage(html_message, images):
    dom = html.fromstring(html_message)
    image_tags = dom.xpath(r'//img')
    for image_tag in image_tags:
        cid = image_tag.attrib['src'].replace('cid:', '')
        if cid in images:
            image_tag.attrib['src'] = images[cid]
        else:
            image_tag.attrib['alt'] = '添付画像埋め込み失敗'
    html_message = html.tostring(dom, encoding='utf-8').decode('utf-8')
    return html_message


def attachImagesOntoMessage(plain_message, images):
    attachment_text = ''
    counter = 1
    for cid, b64payload in images.items():
        attachment_text += '<p>添付%s</p>' % counter
        counter += 1
        attachment_text += '<img src="%s">' % b64payload

    plain_message += '<hr>'
    plain_message += attachment_text

    return plain_message


def file_validation(file_path):
    '''ファイルのバリデーション'''
    if not os.path.exists(file_path):
        raise click.ClickException(f'The file({file_path}) does not exists')


def email2html(file_path):
    '''メールファイルのパスを受け取って、plain/text と plain/html を HTML 形式にして返す'''
    file_validation(file_path)

    with open(file_path, 'rb') as fp:
        em = email.message_from_bytes(fp.read())

    images = {}
    message = {}
    for part in em.walk():
        maintype = part.get_content_maintype()
        if maintype == 'text':
            subtype = part.get_content_subtype()
            # text/plain の処理
            if subtype == 'plain':
                message['plain'] = textPlainConv(part)
            # text/html の処理
            elif subtype == 'html':
                message['html'] = textHtmlConv(part)

        # 添付画像の処理
        ## 画像が base64 エンコードされたデータの時のみ、
        ## content-id をキーとして images に格納する
        if maintype == 'image':
            content_id, b64payload = imgConv(part)
            if content_id:
                images[content_id] = b64payload

    if images:
        if 'html' in message:
            message['html'] = buryImagesIntoMessage(message['html'], images)
        if 'plain' in message:
            message['plain'] = attachImagesOntoMessage(message['plain'], images)

    return message

@creator_grp.command()
@click.option('--file-path', required=True, help='メールファイルのパス')
def convert(file_path, **kwargs):
    '''渡されたメールソースを html に変換する'''
    message = email2html(file_path)
    click.echo(f'[Info] {message}')
    click.echo('[Info] Done!')


@creator_grp.command()
@click.option('--original-dir', required=True, default=r'./original_files', help='メールファイルが入っているフォルダのパス')
@click.option('--output-dir', required=True, default=r'./output', help='HTML 変換後のファイルが入るフォルダのパス')
def bulkConvert(original_dir, output_dir, **kwargs):
    '''original-dir 内にあるメールファイルを html 変換し output-dir 内に格納する'''
    files = os.listdir(original_dir)
    for file_name in files:
        if file_name == '.gitkeep':
            continue
        file_path = os.path.join(original_dir, file_name)
        message = email2html(file_path)
        if 'plain' in message:
            output_path = os.path.join(output_dir, file_name + '.plain.html')
            with open(output_path, 'w') as fp:
                fp.write(message['plain'])
        if 'html' in message:
            output_path = os.path.join(output_dir, file_name + '.html.html')
            with open(output_path, 'w') as fp:
                fp.write(message['html'])

    click.echo(f'[Info] Done!')

def main():
    creator_grp()


if __name__ == "__main__":
    main()
