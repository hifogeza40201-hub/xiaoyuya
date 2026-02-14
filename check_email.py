#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import imaplib
import email
from email.header import decode_header
import json

# QQ邮箱配置
IMAP_SERVER = "imap.qq.com"
IMAP_PORT = 993
EMAIL = "9100182@qq.com"
PASSWORD = "vlqvsnfkjlgzbhee"

def decode_str(s):
    """解码邮件主题/发件人等"""
    if s is None:
        return ""
    value, charset = decode_header(s)[0]
    if isinstance(value, bytes):
        if charset:
            value = value.decode(charset)
        else:
            value = value.decode('utf-8')
    return value

def get_email_content(msg):
    """获取邮件正文内容"""
    content = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    if charset:
                        content = body.decode(charset)
                    else:
                        content = body.decode('utf-8')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True)
            charset = msg.get_content_charset()
            if charset:
                content = body.decode(charset)
            else:
                content = body.decode('utf-8')
        except:
            pass
    return content[:500] if content else "(无正文或无法解析)"

def main():
    try:
        # 连接IMAP服务器
        print("正在连接 QQ 邮箱...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, PASSWORD)
        print("登录成功！")
        print()
        
        # 选择收件箱
        mail.select("INBOX")
        
        # 搜索未读邮件
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            print("搜索邮件失败")
            return
        
        msg_ids = messages[0].split()
        
        if not msg_ids:
            print("没有未读邮件")
            return
        
        print("找到 {} 封未读邮件".format(len(msg_ids)))
        print("=" * 60)
        
        results = []
        
        for i, msg_id in enumerate(msg_ids[:10], 1):  # 最多读取10封
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 解析邮件信息
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date = msg["Date"] or "未知时间"
            content = get_email_content(msg)
            
            email_info = {
                "index": i,
                "subject": subject or "(无主题)",
                "from": from_addr,
                "date": date,
                "content": content
            }
            results.append(email_info)
            
            print()
            print("【邮件 {}】".format(i))
            print("发件人: {}".format(from_addr))
            print("主题: {}".format(subject or "(无主题)"))
            print("时间: {}".format(date))
            preview = content[:150].replace('\n', ' ').replace('\r', '')
            print("预览: {}...".format(preview))
            print("-" * 60)
        
        print()
        print("共读取 {} 封未读邮件".format(len(results)))
        
        # 保存结果供后续使用
        with open("emails_summary.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        mail.logout()
        
    except Exception as e:
        print("错误: {}".format(e))

if __name__ == "__main__":
    main()
