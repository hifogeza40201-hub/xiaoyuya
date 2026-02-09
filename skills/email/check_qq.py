import imaplib
import email
from email.header import decode_header
import ssl

def check_qq_email():
    imap_server = "imap.qq.com"
    email_address = "9100182@qq.com"
    auth_code = "ldiombpprgrbcbbb"
    
    try:
        # 连接IMAP服务器 (SSL)
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        
        # 登录
        mail.login(email_address, auth_code)
        
        # 选择收件箱
        mail.select("inbox")
        
        # 搜索未读邮件
        status, messages = mail.search(None, "UNSEEN")
        
        unread_list = []
        if status == "OK":
            msg_ids = messages[0].split()
            unread_count = len(msg_ids)
            
            print(f"未读邮件数量: {unread_count}")
            
            # 获取最新的5封未读邮件
            for i, msg_id in enumerate(msg_ids[-5:]):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # 解码主题
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")
                        
                        # 获取发件人
                        from_addr = msg.get("From")
                        
                        # 获取日期
                        date = msg.get("Date")
                        
                        unread_list.append({
                            "subject": subject,
                            "from": from_addr,
                            "date": date
                        })
        
        mail.close()
        mail.logout()
        
        return unread_list
        
    except Exception as e:
        print(f"错误: {e}")
        return []

if __name__ == "__main__":
    emails = check_qq_email()
    for i, e in enumerate(emails, 1):
        print(f"{i}. {e['subject']}")
        print(f"   发件人: {e['from']}")
        print(f"   时间: {e['date']}")
        print()
