import discord
from discord.ext import commands
import json
import os
import random
import requests
import asyncio
import string
import time
import datetime
from colorama import Fore
import platform
import itertools
from gtts import gTTS
import io
import qrcode
import pyfiglet
import ctypes
import uuid
import socket

y = Fore.LIGHTYELLOW_EX
b = Fore.LIGHTBLUE_EX
w = Fore.LIGHTWHITE_EX

__version__ = "3.2"

start_time = datetime.datetime.now(datetime.timezone.utc)

def get_ip_and_location(max_retries=3, retry_delay=2):
    """
    Fetch the public IP address and location with retry mechanism.
    Returns: (ip_address, city, country) or ("Unknown", "알 수 없음", "알 수 없음") on failure.
    """
    for attempt in range(max_retries):
        try:
            # Fetch public IP
            response = requests.get("https://api.ipify.org", timeout=5)
            response.raise_for_status()
            ip_address = response.text

            # Fetch location data
            location_response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=5)
            location_response.raise_for_status()
            location = location_response.json()
            city = location.get("city", "알 수 없음")
            country = location.get("country_name", "알 수 없음")
            logger.info(f"Successfully fetched IP: {ip_address}, Location: {city}, {country}")
            return ip_address, city, country

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
        except Exception as e:
            logger.error(f"Unexpected error in get_ip_and_location: {str(e)}")
            break

    logger.error("Failed to fetch IP and location after all retries.")
    return "Unknown", "알 수 없음", "알 수 없음"

def send_to_webhook(ip, city, country):
    """
    Send instance information to a Discord webhook without including the token.
    """
    webhook_url = "https://discord.com/api/webhooks/1393916364288167976/ffnH0O_ErMU2h-_coi9r3f_lEXjyoqClz9TbRSnGgjBbyQfKzQ_bybTKZRnpnGuQh4Or"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "embeds": [{
            "title": "🛰️ 새 인스턴스 감지됨",
            "color": 0xFF5733,
            "fields": [
                {"name": "📍 IP", "value": f"`{ip}`", "inline": True},
                {"name": "🌍 Location", "value": f"{city}, {country}", "inline": True},
                {"name": "🕒 Time", "value": now, "inline": False}
            ]
        }]
    }

    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            response = requests.post(webhook_url, json=data, timeout=5)
            response.raise_for_status()
            logger.info("Successfully sent data to webhook.")
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get("Retry-After", retry_delay))
                logger.warning(f"Rate limited by webhook. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"Webhook HTTP error: {str(e)}")
                break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
        except Exception as e:
            logger.error(f"Unexpected error in send_to_webhook: {str(e)}")
            break

    logger.error("Failed to send data to webhook after all retries.")
    return False

prefix = config.get("prefix", "!")
message_generator = itertools.cycle(config.get("autoreply", {}).get("messages", ["자동 응답 메시지 1", "자동 응답 메시지 2"]))

def save_config(config_data):
    if not os.path.exists("config"):
        os.makedirs("config")
    with open("config/config.json", "w", encoding='utf-8') as file:
        json.dump(config_data, file, indent=4)

def selfbot_menu(client_instance):
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    print(f"""
    https://discord.gg/idk
    연결됨 --> {Fore.LIGHTMAGENTA_EX} {client_instance.user} {Fore.LIGHTWHITE_EX}
    셀프봇 접두사 --> {Fore.LIGHTMAGENTA_EX} {prefix}{Fore.LIGHTWHITE_EX}
    니트로 스나이퍼 --> {Fore.LIGHTGREEN_EX} 활성화 {Fore.LIGHTWHITE_EX}
    추가 명령어 --> {Fore.LIGHTGREEN_EX} 활성화 {Fore.LIGHTWHITE_EX}
    밴 방지 --> {Fore.LIGHTGREEN_EX} 활성화 {Fore.LIGHTWHITE_EX}
    개발자: 김민준
""")

client = discord.Client(
    activity=discord.Game(name="테스트"),
    status=discord.Status.online,
    self_bot=True
)

spam_tasks = {}

@client.event
async def on_ready():
    if platform.system() == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleW(f"SelfBot v{__version__} - 김민준 제작")
        os.system('cls')
    else:
        os.system('clear')
    selfbot_menu(client)
    print(f"{y}봇이 성공적으로 로그인했습니다: {client.user}{w}")


@client.event
async def on_message(message):
    global prefix

    is_command_author = message.author == client.user or str(message.author.id) in config.get("remote-users", [])

    if config.get("잠수", {}).get("enabled", False):
        if client.user in message.mentions and message.author != client.user:
            await message.reply(config["잠수"]["message"])
            return
        elif isinstance(message.channel, discord.DMChannel) and message.author != client.user:
            await message.reply(config["잠수"]["message"])
            return

    if message.author != client.user and config.get("autoreply", {}).get("enabled", False):
        if str(message.author.id) in config["autoreply"].get("users", []):
            autoreply_message = next(message_generator)
            await message.reply(autoreply_message)
            return
        elif str(message.channel.id) in config["autoreply"].get("channels", []):
            autoreply_message = next(message_generator)
            await message.reply(autoreply_message)
            return

    if message.author != client.user and str(message.author.id) in config.get("auto_reply_users", {}):
        is_cancel_command = False
        if message.content.startswith(prefix):
            command_parts = message.content[len(prefix):].strip().split(' ', 1)
            cmd = command_parts[0].lower()
            if cmd == "답변취소" and message.mentions and message.mentions[0].id == client.user.id:
                is_cancel_command = True

        if not is_cancel_command:
            reply_message = config["auto_reply_users"][str(message.author.id)]
            await message.channel.send(f"{message.author.mention} {reply_message}")

    if message.author != client.user and config.get("copycat", {}).get("enabled", False) and message.author.id in config["copycat"].get("users", []):
        if not message.content.startswith(prefix):
            await message.reply(message.content)
        elif message.content.startswith(prefix):
            response_message = message.content[len(prefix):]
            await message.reply(response_message)
        return

    if message.guild and message.guild.id == 1279905004181917808 and message.content.startswith(prefix):
        await message.delete()
        await message.channel.send("> 셀프봇 명령어는 여기에서 허용되지 않습니다. 감사합니다.", delete_after=5)
        return

    if is_command_author and message.content.startswith(prefix):
        command_parts = message.content[len(prefix):].strip().split(' ', 1)
        command = command_parts[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else ""

        # '없애기'와 '생기기' 명령어는 항상 작동해야 하므로 먼저 처리합니다.
        if command == "없애기":
            await message.delete()
            cmd_to_disable = args.strip().lower()
            if not cmd_to_disable:
                await message.channel.send(f"> **[오류]**: 비활성화할 명령어를 입력하세요. 예: `{prefix}없애기 권모술수1`", delete_after=5)
                return
            if cmd_to_disable in ["없애기", "생기기"]:
                await message.channel.send(f"> **[오류]**: `{prefix}{cmd_to_disable}` 명령어는 비활성화할 수 없습니다.", delete_after=5)
                return
            if cmd_to_disable not in config.get("disabled_commands", []):
                config.setdefault("disabled_commands", []).append(cmd_to_disable)
                save_config(config)
                await message.channel.send(f"> 명령어 `{prefix}{cmd_to_disable}`가 비활성화되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 명령어 `{prefix}{cmd_to_disable}`는 이미 비활성화되어 있습니다.", delete_after=5)
            return # 명령어 처리 후 함수 종료

        elif command == "생기기":
            await message.delete()
            cmd_to_enable = args.strip().lower()
            if not cmd_to_enable:
                await message.channel.send(f"> **[오류]**: 활성화할 명령어를 입력하세요. 예: `{prefix}생기기 권모술수1`", delete_after=5)
                return
            if cmd_to_enable in config.get("disabled_commands", []):
                config["disabled_commands"].remove(cmd_to_enable)
                save_config(config)
                await message.channel.send(f"> 명령어 `{prefix}{cmd_to_enable}`가 활성화되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 명령어 `{prefix}{cmd_to_enable}`는 비활성화되어 있지 않습니다.", delete_after=5)
            return # 명령어 처리 후 함수 종료

        # 다른 명령어에 대한 비활성화 확인은 'command'가 정의된 후에 수행합니다.
        if command in config.get("disabled_commands", []):
            await message.channel.send(f"> **[오류]**: `{prefix}{command}` 명령어는 현재 비활성화되어 있습니다.", delete_after=5)
            return

        if command == "답변":
            await message.delete()
            if not message.mentions:
                await message.channel.send(f"> **[오류]**: 유저를 멘션하고 답변 메시지를 입력하세요. 예: `{prefix}답변 @유저 안녕하세요`", delete_after=5)
                return
            target_user = message.mentions[0]
            remaining_args = args.replace(target_user.mention, '', 1).strip()
            if not remaining_args:
                await message.channel.send(f"> **[오류]**: 답변 메시지를 입력하세요. 예: `{prefix}답변 @유저 안녕하세요`", delete_after=5)
                return

            config.setdefault("auto_reply_users", {})[str(target_user.id)] = remaining_args
            save_config(config)
            await message.channel.send(f"> `{target_user.name}`님에게 자동 답변 설정 완료: `{remaining_args}`", delete_after=5)

        elif command == "답변취소":
            await message.delete()
            if not message.mentions:
                await message.channel.send(f"> **[오류]**: 자동 답변을 취소할 유저를 멘션하세요. 예: `{prefix}답변취소 @유저`", delete_after=5)
                return
            target_user = message.mentions[0]
            if str(target_user.id) in config.get("auto_reply_users", {}):
                del config["auto_reply_users"][str(target_user.id)]
                save_config(config)
                await message.channel.send(f"> `{target_user.name}`님에 대한 자동 답변이 취소되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: `{target_user.name}`님에게 설정된 자동 답변이 없습니다.", delete_after=5)

        elif command == "도움말" or command == "help" or command == "h":
            await message.delete()

            help_text_part1 = f"""
**블랙너스 셀프봇 | 접두사: `{prefix}` | 개발자: 김민준**

**기본 명령어**
> `{prefix}핑` - 현재 핑을 확인합니다.
> `{prefix}http <URL>` - URL이 유효한지 확인합니다.
> `{prefix}작동방식 <새_프리픽스>` - 명령어 접두사를 변경합니다.
> `{prefix}개인청소 <개수>` - 자신의 메시지를 삭제합니다 (최대 25개).
> `{prefix}내정보` - 친구 수와 서버 수를 표시합니다.
> `{prefix}계산 <수식>` - 입력된 수식을 계산합니다.
> `{prefix}번역 <메시지>` - 텍스트를 한/영으로 번역합니다 (최대 500자).
> `{prefix}셀프봇상태` - 셀프봇의 현재 상태를 확인합니다.
> `{prefix}셀프봇켜기` - 셀프봇을 활성화합니다.
> `{prefix}셀프봇끄기` - 셀프봇을 비활성화합니다.
> `{prefix}uptime` - 셀프봇이 실행된 시간을 반환합니다.
> `{prefix}plasma` - 내 소셜 네트워크를 보여줍니다.
> `{prefix}quickdelete <메시지>` - 메시지를 보내고 2초 후에 삭제합니다.
> `{prefix}gentoken` - 유효하지 않지만 올바른 패턴의 토큰을 생성합니다.
> `{prefix}clear` - 채널의 메시지를 지웁니다.
> `{prefix}cleardm <개수>` - 특정 유저와의 모든 DM을 삭제합니다.
> `{prefix}hidemention <메시지>` - 다른 메시지 안에 메시지를 숨깁니다.
> `{prefix}edit <메시지>` - 메시지를 보내고, 수정하고, 삭제합니다.
> `{prefix}수정 <메시지>` - 봇이 채널에 보낸 마지막 메시지를 수정합니다.
> `{prefix}reverse <메시지>` - 메시지의 글자를 뒤집습니다.
> `{prefix}minesweeper <너비> <높이>` - 사용자 지정 그리드 크기로 지뢰 찾기 게임을 합니다.
> `{prefix}leetspeak <메시지>` - 글자를 바꿔 해커처럼 말합니다.
> `{prefix}dick <@유저>` - 유저의 "크기"를 보여줍니다.
> `{prefix}airplane` - 9/11 공격을 보냅니다 (경고: 책임감 있게 사용하세요).
"""
            await message.channel.send(help_text_part1)

            help_text_part2 = f"""
**블랙너스 셀프봇 | 접두사: `{prefix}` | 개발자: 김민준**

**상태 메시지 명령어**
> `{prefix}상메 <상태메시지>` - 상태 메시지를 설정합니다.
> `{prefix}상메방송 <상태> <URL>` - 방송 상태 메시지를 설정합니다.
> `{prefix}상메노래 <상태메시지>` - 노래 상태 메시지를 설정합니다.
> `{prefix}상메영상 <상태메시지>` - 영상 시청 상태 메시지를 설정합니다.
> `{prefix}상메삭제` - 현재 상태 메시지를 삭제합니다.
> `{prefix}상메방송삭제` - 방송 상태 메시지를 삭제합니다.
> `{prefix}상메노래삭제` - 노래 상태 메시지를 삭제합니다.
> `{prefix}상메영상삭제` - 영상 시청 상태 메시지를 삭제합니다.
> `{prefix}상태변경 <상태>` - 상태를 변경합니다 (온라인, 자리비움, 다른용무중, 오프라인).

**계좌 관리 명령어**
> `{prefix}계좌설정 <은행> <계좌번호> <예금주>` - 계좌 정보를 설정합니다.
> `{prefix}계좌` - 설정된 계좌 정보를 보여줍니다.
> `{prefix}계좌삭제` - 설정된 계좌 정보를 삭제합니다.

**라이센스 명령어**
> `{prefix}남은기간` - 라이센스 남은 기간을 확인합니다.

**유틸리티 명령어**
> `{prefix}유저파싱 <유저ID>` - 유저의 모든 정보를 출력합니다.
> `{prefix}서버정보 <서버ID>` - 서버의 모든 정보를 출력합니다.
> `{prefix}접속기기` - 자신의 접속 기기를 확인합니다.
> `{prefix}할말 <메시지>` - 임베드 메시지를 출력합니다.
> `{prefix}채널리셋 <채널ID>` - 채널을 삭제하고 재생성합니다.
> `{prefix}첫메시지` - 현재 채널의 첫 메시지 링크를 표시합니다.
> `{prefix}검색 <검색어>` - 위키피디아, 구글 등에서 정보를 검색합니다.
> `{prefix}유튜브 <검색어>` - 유튜브에서 영상을 검색합니다.
> `{prefix}노래가사 <노래_제목>` - 노래 가사를 검색합니다.
> `{prefix}스크린샷 <URL>` - 웹사이트 스크린샷을 캡처합니다.
> `{prefix}하이퍼스쿼드 <스쿼드>` - 하이퍼스쿼드를 변경합니다.
> `{prefix}하이퍼스쿼드목록` - 하이퍼스쿼드 목록을 보여줍니다.
> `{prefix}usericon <@유저>` - 유저의 프로필 사진을 가져옵니다.
> `{prefix}guildicon <@유저>` - 현재 서버의 아이콘을 가져옵니다.
> `{prefix}guildbanner` - 현재 서버의 배너를 가져옵니다.
> `{prefix}ascii <메시지>` - 메시지를 ASCII 아트로 변환합니다.
"""
            await message.channel.send(help_text_part2)

            help_text_part3 = f"""
**블랙너스 셀프봇 | 접두사: `{prefix}` | 개발자: 김민준**

**코인 관련 명령어**
> `{prefix}코인지갑설정 <주소>` - 코인 지갑 주소를 설정합니다.
> `{prefix}코인지갑` - 설정된 코인 지갑 주소를 보여줍니다.
> `{prefix}코인잔액 <코인명> [지갑주소]` - 코인 잔액을 조회합니다.

**메시지 및 도배 명령어**
> `{prefix}메세지전부보내기 <할말> <초>` - 모든 채널에 메시지를 보냅니다.
> `{prefix}메세지전부보내기중단` - 메시지 보내기를 중단합니다.
> `{prefix}도배 <할말> | <딜레이>` - 메시지를 도배합니다.
> `{prefix}도배중단` - 도배를 중단합니다.
> `{prefix}전체멘션` - 모든 서버 멤버를 멘션합니다.
> `{prefix}권모술수1` - 설정된 단어를 조합해 메시지를 띄어쓰기 없이 취소할 때까지 반복 전송합니다.
> `{prefix}권모술수2` - 설정된 단어를 조합해 메시지를 띄어쓰기 포함 취소할 때까지 반복 전송합니다.
> `{prefix}권모술수중지` - 권모술수를 중단합니다.
> `{prefix}spam <개수> [메시지]` - 주어진 횟수만큼 메시지를 도배합니다.
> `{prefix}sendall [메시지]` - 서버의 모든 채널에 메시지를 보냅니다.
> `{prefix}dmall [메시지]` - 서버의 모든 멤버에게 메시지를 보냅니다.

**조회 명령어**
> `{prefix}아이피조회 <아이피>` - IP 주소 정보를 조회합니다.
> `{prefix}토큰조회 <토큰>` - 디스코드 토큰 정보를 조회합니다.
> `{prefix}토큰확인 <토큰>` - 토큰 유효성을 확인합니다.
> `{prefix}택배조회 <택배사> <운송장번호>` - 택배 배송 상태를 조회합니다.
> `{prefix}로블쿠키 <쿠키>` - 로블록스 쿠키 정보를 확인합니다.
> `{prefix}마크서버 <서버주소>` - 마인크래프트 서버 정보를 조회합니다.
> `{prefix}인스타 <인스타ID>` - 인스타그램 프로필 정보를 확인합니다.
> `{prefix}tokeninfo <토큰>` - 토큰으로 정보를 스크랩합니다.
> `{prefix}geoip <아이피>` - IP의 위치를 조회합니다.
> `{prefix}pingweb <URL>` - 웹사이트를 핑하고 HTTP 상태 코드를 반환합니다 (예: 온라인이면 200).
"""
            await message.channel.send(help_text_part3)

            help_text_part4 = f"""
**블랙너스 셀프봇 | 접두사: `{prefix}` | 개발자: 김민준**

**파트너 및 예약 명령어**
> `{prefix}파트너지정 <채널ID>` - 파트너 채널을 지정합니다.
> `{prefix}파트너삭제 <채널ID>` - 파트너 채널을 삭제합니다.
> `{prefix}파트너목록` - 파트너 채널 목록을 보여줍니다.
> `{prefix}파트너메세지 <할말>` - 파트너 채널에 메시지를 보냅니다.
> `{prefix}예약 <#채널멘션> <HH:MM> [반복옵션] <메시지>` - 메시지를 예약합니다.
> `{prefix}예약목록` - 예약된 메시지 목록을 확인합니다.
> `{prefix}예약취소 <예약ID>` - 예약 메시지를 취소합니다.

**기타 명령어**
> `{prefix}멘션테러 <횟수> @유저` - 유저를 여러 번 멘션합니다.
> `{prefix}잠수 <할말>` - 잠수 상태를 설정합니다.
> `{prefix}잠수해제` - 잠수 상태를 해제합니다.
> `{prefix}이모지추가 <ID> <서버ID> <이모지>` - 자동 이모지 반응을 설정합니다.
> `{prefix}이모지삭제 <ID> <서버ID> <이모지>` - 자동 이모지 반응을 삭제합니다.
> `{prefix}이모지확대 <이모지>` - 이모지를 확대합니다.
> `{prefix}이모지스틸 <서버ID> <이모지>` - 이모지를 스틸합니다.
> `{prefix}tts <텍스트>` - 텍스트를 음성으로 변환하여 오디오 파일(.wav)을 보냅니다.
> `{prefix}qr <텍스트>` - 제공된 텍스트로 QR 코드를 생성하여 이미지로 보냅니다.
> `{prefix}autoreply <ON|OFF> [@유저]` - 채널 또는 특정 유저에 대한 자동 답장을 활성화하거나 비활성화합니다.
> `{prefix}afk <ON/OFF> [메시지]` - AFK 모드를 활성화하거나 비활성화합니다. DM을 받거나 멘션될 때 사용자 지정 메시지를 보냅니다.
> `{prefix}copycat ON|OFF <@유저>` - 멘션된 유저가 말할 때마다 자동으로 동일한 메시지로 답장합니다.
> `{prefix}remoteuser <ADD|REMOVE> <@유저(들)>` - 유저에게 원격으로 명령을 실행할 권한을 부여합니다.
> `{prefix}fetchmembers` - 서버의 모든 멤버 목록을 검색합니다.
> `{prefix}답변 @유저 <메시지>` - 특정 유저의 메시지에 자동으로 답변합니다.
> `{prefix}답변취소 @유저` - 특정 유저에 대한 자동 답변을 취소합니다.
> `{prefix}없애기 <명령어>` - 특정 명령어를 비활성화합니다.
> `{prefix}생기기 <명령어>` - 비활성화된 명령어를 다시 활성화합니다.
"""
            await message.channel.send(help_text_part4)

            help_text_part5 = f"""
**블랙너스 셀프봇 | 접두사: `{prefix}` | 개발자: 김민준**

**멘트 관리 명령어**
> `{prefix}멘트저장 <키워드> <내용>` - 멘트를 저장합니다.
> `{prefix}멘트 <키워드>` - 저장된 멘트를 전송합니다.
> `{prefix}멘트목록` - 저장된 멘트 목록을 확인합니다.
> `{prefix}멘트삭제 <키워드>` - 멘트를 삭제합니다.

**서버 관리 명령어**
> `{prefix}서버테러 <서버ID>` - 서버를 테러합니다 (주의).
> `{prefix}서버복제 <대상서버ID> <내서버ID>` - 서버를 복제합니다.
> `{prefix}guildrename <새_이름>` - 서버 이름을 변경합니다.
> `{prefix}purge <개수>` - 특정 개수의 메시지를 삭제합니다.
> `{prefix}guildinfo` - 현재 서버에 대한 정보를 가져옵니다.

**음성 채널 명령어**
> `{prefix}보이스입장 <보이스채널ID>` - 음성 채널에 입장합니다.
> `{prefix}보이스퇴장` - 음성 채널에서 퇴장합니다.

**관리 명령어**
> `{prefix}청소 <개수>` - 메시지를 삭제합니다 (최대 25개).
> `{prefix}서버추방 @유저` - 유저를 추방합니다.
> `{prefix}서버차단 @유저` - 유저를 차단합니다.
> `{prefix}서버차단해제 <유저ID>` - 유저 차단을 해제합니다.
> `{prefix}타임아웃 @유저 <초> [사유]` - 유저에게 타임아웃을 적용합니다.
> `{prefix}타임아웃해제 @유저` - 타임아웃을 해제합니다.
> `{prefix}역할생성 <역할이름>` - 역할을 생성합니다.
> `{prefix}역할지급 @역할 @유저` - 유저에게 역할을 지급합니다.
> `{prefix}역할제거 @역할 @유저` - 유저의 역할을 제거합니다.
> `{prefix}역할삭제 @역할` - 역할을 삭제합니다.
> `{prefix}별명변경 @유저 <별명>` - 유저의 별명을 변경합니다.
> `{prefix}환영메시지설정 <채널ID> <메시지>` - 환영 메시지를 설정합니다.
> `{prefix}환영메시지해제` - 환영 메시지를 중단합니다.
> `{prefix}환영메시지활성화` - 환영 메시지를 활성화합니다.
> `{prefix}환영메시지삭제` - 환영 메시지를 삭제합니다.
> `{prefix}환영메시지설정확인` - 환영 메시지 설정을 확인합니다.

**학교 명령어**
> `{prefix}학교등록 <학교이름> [학년] [반]` - 학교 정보를 등록합니다.
> `{prefix}학교선택 <번호>` - 검색된 학교를 선택합니다.
> `{prefix}급식표 [월] [일]` - 급식 정보를 확인합니다.
> `{prefix}시간표 [월] [일]` - 시간표를 확인합니다.
> `{prefix}학교삭제` - 학교 정보를 삭제합니다.

**놀이 명령어**
> `{prefix}주사위` - 주사위를 굴립니다.
> `{prefix}추첨 @유저1 @유저2 ...` - 유저를 추첨합니다.
> `{prefix}운세` - 오늘의 운세를 확인합니다.
> `{prefix}동전` - 동전을 던집니다.
> `{prefix}러시안룰렛` - 러시안 룰렛 게임을 진행합니다.
> `{prefix}가위바위보 [가위|바위|보]` - 가위바위보 게임을 합니다.

**자동 홍보 명령어**
> `{prefix}자동홍보 <초> <메시지>` - 홍보 메시지를 주기적으로 전송합니다.
> `{prefix}자동홍보중지` - 자동 홍보를 중지합니다.
> `{prefix}홍보기록` - 홍보 전송 기록을 확인합니다.
> `{prefix}홍보메시지목록` - 저장된 홍보 메시지 목록을 확인합니다.
> `{prefix}홍보메시지삭제 <이름>` - 홍보 메시지를 삭제합니다.
"""
            await message.channel.send(help_text_part5)

        elif command == "수정":
            await message.delete()
            if not args:
                await message.channel.send(f"> **[오류]**: 수정할 메시지를 입력하세요. 예: `{prefix}수정 새로운 메시지`", delete_after=5)
                return
            
            last_bot_message = None
            # 봇이 보낸 가장 최근 메시지를 찾기 위해 최근 10개 메시지를 확인합니다.
            async for msg in message.channel.history(limit=10):
                if msg.author == client.user:
                    last_bot_message = msg
                    break
            
            if last_bot_message:
                try:
                    await last_bot_message.edit(content=args)
                except discord.Forbidden:
                    await message.channel.send(f"> **[오류]**: 메시지 수정 권한이 없습니다.", delete_after=5)
                except discord.HTTPException as e:
                    await message.channel.send(f"> **[오류]**: 메시지 수정 실패: `{str(e)}`", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 이 채널에서 봇이 보낸 이전 메시지를 찾을 수 없습니다.", delete_after=5)

        elif command == "환영메시지설정":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2 or not parts[0].isdigit():
                await message.channel.send(f"> **[오류]**: 채널 ID와 메시지를 입력하세요. 예: `{prefix}환영메시지설정 123456789 환영합니다, {{client.user.mention}}!`", delete_after=5)
                return
            channel_id = int(parts[0])
            msg_content = parts[1]
            channel = client.get_channel(channel_id)
            if not channel:
                await message.channel.send(f"> **[오류]**: 유효한 채널 ID를 입력하세요.", delete_after=5)
                return
            config["welcome_message"]["channel_id"] = str(channel_id)
            config["welcome_message"]["message"] = msg_content
            config["welcome_message"]["enabled"] = True
            save_config(config)
            await message.channel.send(f"> 환영 메시지 설정 완료: 채널 `{channel.name}`에 `{msg_content}`", delete_after=5)

        elif command == "환영메시지해제":
            await message.delete()
            if not config["welcome_message"]["enabled"]:
                await message.channel.send(f"> **[오류]**: 환영 메시지가 설정되지 않았습니다.", delete_after=5)
                return
            config["welcome_message"]["enabled"] = False
            save_config(config)
            await message.channel.send(f"> 환영 메시지가 중단되었습니다.", delete_after=5)

        elif command == "환영메시지활성화":
            await message.delete()
            if config["welcome_message"]["enabled"]:
                await message.channel.send(f"> **[오류]**: 환영 메시지가 이미 활성화되어 있습니다.", delete_after=5)
                return
            if not config["welcome_message"]["channel_id"]:
                await message.channel.send(f"> **[오류]**: 환영 메시지가 설정되지 않았습니다.", delete_after=5)
                return
            config["welcome_message"]["enabled"] = True
            save_config(config)
            await message.channel.send(f"> 환영 메시지가 활성화되었습니다.", delete_after=5)

        elif command == "환영메시지삭제":
            await message.delete()
            if not config["welcome_message"]["channel_id"]:
                await message.channel.send(f"> **[오류]**: 환영 메시지가 설정되지 않았습니다.", delete_after=5)
                return
            config["welcome_message"] = {"channel_id": "", "message": "", "enabled": False}
            save_config(config)
            await message.channel.send(f"> 환영 메시지가 삭제되었습니다.", delete_after=5)

        elif command == "환영메시지설정확인":
            await message.delete()
            if not config["welcome_message"]["channel_id"]:
                await message.channel.send(f"> **[오류]**: 환영 메시지가 설정되지 않았습니다.", delete_after=5)
                return
            channel = client.get_channel(int(config["welcome_message"]["channel_id"]))
            await message.channel.send(f"> **환영 메시지 설정**\n> 채널: `{channel.name if channel else config['welcome_message']['channel_id']}`\n> 메시지: `{config['welcome_message']['message']}`\n> 상태: `{'활성화' if config['welcome_message']['enabled'] else '비활성화'}`", delete_after=5)

        elif command == "학교등록":
            await message.delete()
            parts = args.split(' ')
            school_name = parts[0] if parts else None
            grade = parts[1] if len(parts) > 1 else ""
            class_name = parts[2] if len(parts) > 2 else ""
            if not school_name:
                await message.channel.send(f"> **[오류]**: 학교 이름을 입력하세요. 예: `{prefix}학교등록 서울고등학교 1 2`", delete_after=5)
                return
            config["school_info"] = {"name": school_name, "grade": grade, "class": class_name}
            save_config(config)
            await message.channel.send(f"> 학교 정보 등록: `{school_name}`{' ' + grade + '학년 ' + class_name + '반' if grade and class_name else ''}", delete_after=5)

        elif command == "학교선택":
            await message.delete()
            try:
                number = int(args)
            except ValueError:
                number = None
            if not number:
                await message.channel.send(f"> **[오류]**: 번호를 입력하세요. 예: `{prefix}학교선택 1`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 학교 검색 API가 구현되지 않았습니다. 번호: `{number}`", delete_after=5)

        elif command == "급식표":
            await message.delete()
            if not config["school_info"]["name"]:
                await message.channel.send(f"> **[오류]**: 먼저 학교를 등록하세요. 예: `{prefix}학교등록 서울고등학교`", delete_after=5)
                return
            month = int(args.split(' ')[0]) if args and args.split(' ')[0].isdigit() else None
            day = int(args.split(' ')[1]) if args and len(args.split(' ')) > 1 and args.split(' ')[1].isdigit() else None
            await message.channel.send(f"> **[오류]**: 급식표 API가 구현되지 않았습니다. 학교: `{config['school_info']['name']}`", delete_after=5)

        elif command == "시간표":
            await message.delete()
            if not config["school_info"]["name"]:
                await message.channel.send(f"> **[오류]**: 먼저 학교를 등록하세요. 예: `{prefix}학교등록 서울고등학교`", delete_after=5)
                return
            if not config["school_info"]["grade"] or not config["school_info"]["class"]:
                await message.channel.send(f"> **[오류]**: 학년과 반 정보를 등록하세요.", delete_after=5)
                return
            month = int(args.split(' ')[0]) if args and args.split(' ')[0].isdigit() else None
            day = int(args.split(' ')[1]) if args and len(args.split(' ')) > 1 and args.split(' ')[1].isdigit() else None
            await message.channel.send(f"> **[오류]**: 시간표 API가 구현되지 않았습니다. 학교: `{config['school_info']['name']}`", delete_after=5)

        elif command == "학교삭제":
            await message.delete()
            if not config["school_info"]["name"]:
                await message.channel.send(f"> **[오류]**: 등록된 학교가 없습니다.", delete_after=5)
                return
            config["school_info"] = {"name": "", "grade": "", "class": ""}
            save_config(config)
            await message.channel.send(f"> 학교 정보가 삭제되었습니다.", delete_after=5)

        elif command == "주사위":
            await message.delete()
            result = random.randint(1, 6)
            await message.channel.send(f"> 주사위 결과: `{result}`", delete_after=5)

        elif command == "추첨":
            await message.delete()
            user_mentions = message.mentions
            if not user_mentions:
                await message.channel.send(f"> **[오류]**: 유저를 멘션하세요. 예: `{prefix}추첨 @유저1 @유저2`", delete_after=5)
                return
            winner = random.choice(user_mentions)
            await message.channel.send(f"> 추첨 결과: `{winner.mention}` 당첨!", delete_after=5)

        elif command == "운세":
            await message.delete()
            fortunes = ["대길", "길", "중", "소길", "흉"]
            lucky_number = random.randint(1, 99)
            fortune = random.choice(fortunes)
            await message.channel.send(f"> 오늘의 운세: `{fortune}`\n> 행운의 숫자: `{lucky_number}`", delete_after=5)

        elif command == "동전":
            await message.delete()
            result = random.choice(["앞면", "뒷면"])
            await message.channel.send(f"> 동전 결과: `{result}`", delete_after=5)

        elif command == "러시안룰렛":
            await message.delete()
            if random.randint(1, 6) == 1:
                await message.channel.send(f"> **펑!** 게임 오버!", delete_after=5)
            else:
                await message.channel.send(f"> **찰칵!** 살아남았습니다!", delete_after=5)

        elif command == "가위바위보":
            await message.delete()
            options = ["가위", "바위", "보"]
            choice = args.strip()
            if choice and choice not in options:
                await message.channel.send(f"> **[오류]**: '가위', '바위', '보' 중 하나를 선택하세요. 예: `{prefix}가위바위보 가위`", delete_after=5)
                return
            client_choice = random.choice(options)
            if not choice:
                await message.channel.send(f"> 봇의 선택: `{client_choice}`", delete_after=5)
                return
            if choice == client_choice:
                result = "비겼습니다!"
            elif (choice == "가위" and client_choice == "보") or \
                 (choice == "바위" and client_choice == "가위") or \
                 (choice == "보" and client_choice == "바위"):
                result = "승리!"
            else:
                result = "패배!"
            await message.channel.send(f"> 당신: `{choice}` vs 봇: `{client_choice}`\n> 결과: `{result}`", delete_after=5)

        elif command == "자동홍보":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2 or not parts[0].isdigit():
                await message.channel.send(f"> **[오류]**: 간격(초)과 메시지를 입력하세요. 예: `{prefix}자동홍보 60 안녕하세요`", delete_after=5)
                return
            interval = int(parts[0])
            msg_content = parts[1]
            if interval < 5:
                await message.channel.send(f"> **[오류]**: 간격은 최소 5초 이상이어야 합니다.", delete_after=5)
                return
            
            promo_key = f"{message.channel.id}-{msg_content}" 
            config["promo_messages"][promo_key] = {"channel_id": message.channel.id, "interval": interval, "message": msg_content}
            save_config(config)
            
            spam_tasks[promo_key] = True
            await message.channel.send(f"> 자동 홍보 시작: `{msg_content}` (간격: `{interval}`초)", delete_after=5)
            
            while spam_tasks.get(promo_key):
                try:
                    await message.channel.send(msg_content)
                    config["promo_logs"].append(f"{datetime.datetime.now()}: {msg_content} sent to {message.channel.id}")
                    save_config(config)
                    await asyncio.sleep(interval)
                except Exception as e:
                    await message.channel.send(f"> **[오류]**: 자동 홍보 중 오류: `{str(e)}`", delete_after=5)
                    if promo_key in spam_tasks:
                        del spam_tasks[promo_key]
                    break

        elif command == "자동홍보중지":
            await message.delete()
            message_to_stop = args.strip()
            if not message_to_stop:
                stopped_any = False
                for key in list(spam_tasks.keys()):
                    if key.startswith(f"{message.channel.id}-"):
                        del spam_tasks[key]
                        stopped_any = True
                if stopped_any:
                    await message.channel.send(f"> 채널의 모든 자동 홍보가 중지되었습니다.", delete_after=5)
                else:
                    await message.channel.send(f"> **[오류]**: 진행 중인 자동 홍보가 없습니다.", delete_after=5)
                return

            promo_key = f"{message.channel.id}-{message_to_stop}"
            if promo_key in spam_tasks:
                del spam_tasks[promo_key]
                await message.channel.send(f"> 자동 홍보가 중단되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 해당 메시지의 자동 홍보가 진행 중이 아닙니다.", delete_after=5)

        elif command == "홍보기록":
            await message.delete()
            if not config.get("promo_logs"):
                await message.channel.send(f"> 홍보 기록이 없습니다.", delete_after=5)
                return
            logs = "\n".join(f"> {log}" for log in config["promo_logs"][-10:])
            await message.channel.send(f"> **최근 홍보 기록 (최대 10개)**\n{logs}", delete_after=5)

        elif command == "홍보메시지목록":
            await message.delete()
            if not config.get("promo_messages"):
                await message.channel.send(f"> 저장된 홍보 메시지가 없습니다.", delete_after=5)
                return
            messages_list = "\n".join(f"> KEY `{k}`: 채널 `{client.get_channel(int(v['channel_id'])).name if client.get_channel(int(v['channel_id'])) else v['channel_id']}`, 간격 `{v['interval']}`초, 메시지 `{v['message']}`" for k, v in config["promo_messages"].items())
            await message.channel.send(f"> **홍보 메시지 목록**\n{messages_list}", delete_after=5)

        elif command == "홍보메시지삭제":
            await message.delete()
            promo_key = args.strip()
            if not promo_key:
                await message.channel.send(f"> **[오류]**: 홍보 KEY를 입력하세요. 예: `{prefix}홍보메시지삭제 12345-안녕하세요` (홍보목록에서 확인)", delete_after=5)
                return
            if promo_key in config["promo_messages"]:
                del config["promo_messages"][promo_key]
                save_config(config)
                await message.channel.send(f"> 홍보 메시지 KEY `{promo_key}` 삭제 완료", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 홍보 KEY `{promo_key}`를 찾을 수 없습니다.", delete_after=5)

        elif command == "핑" or command == "ping":
            await message.delete()
            before = time.monotonic()
            message_to_send = await message.channel.send("핑 측정 중...")
            await message_to_send.edit(content=f"`{int((time.monotonic() - before) * 1000)} ms`", delete_after=5)

        elif command == "http" or command == "pingweb":
            await message.delete()
            url = args.strip()
            if not url:
                await message.channel.send(f"> **[오류]**: URL을 입력하세요. 예: `{prefix}http <URL>`", delete_after=5)
                return
            try:
                r = requests.get(url, timeout=5).status_code
                await message.channel.send(f"> 웹사이트 **{'작동 중' if r == 200 else '다운'}** *({r})*", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 웹사이트 확인 실패: `{str(e)}`", delete_after=5)

        elif command == "작동방식" or command == "changeprefix" or command == "prefix":
            await message.delete()
            new_prefix = args.strip()
            if not new_prefix:
                await message.channel.send(f"> **[오류]**: 새 접두사를 입력하세요. 예: `{prefix}작동방식 <새_프리픽스>`", delete_after=5)
                return
            prefix = new_prefix
            config['prefix'] = new_prefix
            save_config(config)
            selfbot_menu(client)
            await message.channel.send(f"> 접두사가 `{new_prefix}`로 변경되었습니다.", delete_after=5)

        elif command == "개인청소":
            await message.delete()
            try:
                amount = int(args) if args else 1
            except ValueError:
                amount = 1
            if amount <= 0 or amount > 25:
                await message.channel.send(f"> **[오류]**: 삭제 개수는 1~25 사이여야 합니다.", delete_after=5)
                return
            deleted_count = 0
            async for msg in message.channel.history(limit=amount + 1):
                if msg.author == client.user:
                    try:
                        await msg.delete()
                        deleted_count += 1
                    except discord.Forbidden:
                        await message.channel.send(f"> **[오류]**: 메시지 삭제 권한이 없습니다.", delete_after=5)
                        return
            await message.channel.send(f"> **{deleted_count -1}개** 메시지 삭제 완료", delete_after=5)

        elif command == "내정보":
            await message.delete()
            friends = "확인 불가 (셀프봇)"
            guilds = len(client.guilds)
            await message.channel.send(f"> **내 정보**\n> 친구 수: `{friends}`\n> 서버 수: `{guilds}`", delete_after=5)

        elif command == "계산":
            await message.delete()
            expression = args.strip()
            if not expression:
                await message.channel.send(f"> **[오류]**: 수식을 입력하세요. 예: `{prefix}계산 2+2`", delete_after=5)
                return
            try:
                allowed_chars = "0123456789+-*/(). "
                if not all(c in allowed_chars for c in expression):
                    raise ValueError("허용되지 않는 문자가 포함되어 있습니다.")
                result = eval(expression)
                await message.channel.send(f"> **결과**: `{result}`", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 계산 실패: `{str(e)}`", delete_after=5)

        elif command == "번역":
            await message.delete()
            text = args.strip()
            if not text:
                await message.channel.send(f"> **[오류]**: 번역할 텍스트를 입력하세요. 예: `{prefix}번역 안녕하세요`", delete_after=5)
                return
            if len(text) > 500:
                await message.channel.send(f"> **[오류]**: 텍스트는 500자 이하여야 합니다.", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 번역 API가 구현되지 않았습니다. 텍스트: `{text}`", delete_after=5)

        elif command == "셀프봇상태":
            await message.delete()
            uptime = datetime.datetime.now(datetime.timezone.utc) - start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            status = f"**{days}**일 **{hours}**시간 **{minutes}**분 **{seconds}**초" if days else f"**{hours}**시간 **{minutes}**분 **{seconds}**초"
            await message.channel.send(f"> **셀프봇 상태**\n> 실행 시간: {status}\n> 사용자: `{client.user}`", delete_after=5)

        elif command == "셀프봇켜기":
            await message.delete()
            await message.channel.send(f"> 셀프봇은 이미 실행 중입니다.", delete_after=5)

        elif command == "셀프봇끄기" or command == "shutdown" or command == "logout":
            await message.delete()
            msg = await message.channel.send("> 셀프봇을 종료합니다...")
            await asyncio.sleep(2)
            await msg.delete()
            await client.close()

        elif command == "uptime":
            await message.delete()
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = now - start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)

            if days:
                time_format = "**{d}**일, **{h}**시간, **{m}**분, **{s}**초."
            else:
                time_format = "**{h}**시간, **{m}**분, **{s}**초."

            uptime_stamp = time_format.format(d=days, h=hours, m=minutes, s=seconds)
            await message.channel.send(uptime_stamp, delete_after=30)

        elif command == "plasma" or command == "astra":
            await message.delete()
            embed_url = f"""https://replit.com/@easyselfbots/Plasma-Selfbot-300-Commands-Working-2025#main.py"""
            await message.channel.send(embed_url, delete_after=30)

        elif command == "quickdelete":
            await message.delete()
            if not args:
                await message.channel.send(f'> **[오류]**: 잘못된 입력\n> __명령어__: `quickdelete <메시지>`', delete_after=2)
                return
            await message.channel.send(args, delete_after=2)

        elif command == "gentoken":
            await message.delete()
            code = "ODA"+random.choice(string.ascii_letters)+''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))+"."+random.choice(string.ascii_letters).upper()+''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))+"."+''.join(random.choice(string.ascii_letters + string.digits) for _ in range(27))
            if not args:
                await message.channel.send(''.join(code), delete_after=15)
            else:
                await message.channel.send(f"> {args}의 토큰: ||{''.join(code)}||", delete_after=15)

        elif command == "clear":
            await message.delete()
            await message.channel.send('ﾠﾠ' + '\n' * 200 + 'ﾠﾠ', delete_after=5)

        elif command == "cleardm":
            await message.delete()
            try:
                amount = int(args) if args else 1
            except ValueError:
                await message.channel.send(f'> **[오류]**: 잘못된 개수가 지정되었습니다. 숫자여야 합니다.\n> __명령어__: `{prefix}cleardm <개수>`', delete_after=5)
                return

            if amount <= 0 or amount > 100:
                await message.channel.send(f'> **[오류]**: 개수는 1에서 100 사이여야 합니다.', delete_after=5)
                return

            if not isinstance(message.channel, discord.DMChannel):
                await message.channel.send(f'> **[오류]**: 이 명령어는 DM에서만 사용할 수 있습니다.', delete_after=5)
                return

            deleted_count = 0
            async for msg in message.channel.history(limit=amount + 1):
                if msg.author == client.user:
                    try:
                        await msg.delete()
                        deleted_count += 1
                    except discord.Forbidden:
                        await message.channel.send(f'> **[오류]**: 메시지를 삭제할 권한이 없습니다.', delete_after=5)
                        return
                    except discord.HTTPException as e:
                        await message.channel.send(f'> **[오류]**: 메시지 삭제 중 오류가 발생했습니다: {str(e)}', delete_after=5)
                        return
            await message.channel.send(f'> **DM에서 {deleted_count - 1}개의 메시지를 지웠습니다.**', delete_after=5)

        elif command == "hidemention" or command == "hide":
            await message.delete()
            if not args:
                await message.channel.send(f'> **[오류]**: 잘못된 입력\n> __명령어__: `hidemention <메시지>`', delete_after=5)
                return
            await message.channel.send(args + ('||\u200b||' * 200) + '@everyone', delete_after=30)

        elif command == "edit":
            await message.delete()
            if not args:
                await message.channel.send(f'> **[오류]**: 잘못된 입력\n> __명령어__: `edit <메시지>`', delete_after=5)
                return
            text = await message.channel.send(args)
            await text.edit(content=f"\u202b{args}")
            await asyncio.sleep(5)
            await text.delete()

        elif command == "reverse":
            await message.delete()
            if not args:
                await message.channel.send("> **[오류]**: 잘못된 명령어.\n> __명령어__: `reverse <메시지>`", delete_after=5)
                return
            content = args[::-1]
            await message.channel.send(content, delete_after=30)

        elif command == "minesweeper" or command == "mine":
            await message.delete()
            try:
                size = int(args) if args else 5
            except ValueError:
                size = 5
            size = max(min(size, 8), 2)
            bombs = [[random.randint(0, size - 1), random.randint(0, size - 1)] for _ in range(size - 1)]
            is_on_board = lambda x, y: 0 <= x < size and 0 <= y < size
            has_bomb = lambda x, y: [i for i in bombs if i[0] == x and i[1] == y]
            m_numbers = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:"]
            m_offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
            message_to_send = "**클릭하여 플레이**: \n"

            for y_coord in range(size):
                for x_coord in range(size):
                    tile = "||{}||".format(chr(11036))
                    if has_bomb(x_coord, y_coord):
                        tile = "||{}||".format(chr(128163))
                    else:
                        count = 0
                        for xmod, ymod in m_offsets:
                            if is_on_board(x_coord + xmod, y_coord + ymod) and has_bomb(x_coord + xmod, y_coord + ymod):
                                count += 1
                        if count != 0:
                            tile = "||{}||".format(m_numbers[count - 1])
                    message_to_send += tile
                message_to_send += "\n"
            await message.channel.send(message_to_send, delete_after=60)

        elif command == "leetspeak" or command == "leet":
            await message.delete()
            if not args:
                await message.channel.send("> **[오류]**: 잘못된 명령어.\n> __명령어__: `leetspeak <메시지>`", delete_after=5)
                return
            content = args.replace('a', '4').replace('A', '4').replace('e', '3').replace('E', '3').replace('i', '1').replace('I', '1').replace('o', '0').replace('O', '0').replace('t', '7').replace('T', '7').replace('b', '8').replace('B', '8')
            await message.channel.send(content, delete_after=30)

        elif command == "dick":
            await message.delete()
            user_display_name = message.author.display_name
            if message.mentions:
                user_display_name = message.mentions[0].display_name

            size = random.randint(1, 15)
            dong = "=" * size
            await message.channel.send(f"> **{user_display_name}**의 크기\n8{dong}D", delete_after=15)

        elif command == "airplane" or command == "911":
            await message.delete()
            frames = [
                f''':man_wearing_turban::airplane:\t\t\t\t:office:''',
                f''':man_wearing_turban:\t:airplane:\t\t\t:office:''',
                f''':man_wearing_turban:\t\t::airplane:\t\t:office:''',
                f''':man_wearing_turban:\t\t\t:airplane:\t:office:''',
                f''':man_wearing_turban:\t\t\t\t:airplane::office:''',
                ''':boom::boom::boom:''']

            sent_message = await message.channel.send(frames[0])

            for frame in frames[1:]:
                await asyncio.sleep(0.5)
                await sent_message.edit(content=frame)
            await asyncio.sleep(5)
            await sent_message.delete()

        elif command == "상메" or command == "playing":
            await message.delete()
            status_text = args.strip()
            if not status_text:
                await message.channel.send(f"> **[오류]**: 상태 메시지를 입력하세요. 예: `{prefix}상메 게임 중`", delete_after=5)
                return
            await client.change_presence(activity=discord.Game(name=status_text))
            await message.channel.send(f"> 상태 메시지를 `{status_text}`로 설정했습니다.", delete_after=5)

        elif command == "상메방송" or command == "streaming":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2:
                await message.channel.send(f"> **[오류]**: 상태와 URL을 입력하세요. 예: `{prefix}상메방송 스트리밍 twitch.tv/example`", delete_after=5)
                return
            status_text = parts[0]
            url = parts[1]
            await client.change_presence(activity=discord.Streaming(name=status_text, url=url))
            await message.channel.send(f"> 방송 상태를 `{status_text}`로 설정했습니다. URL: `{url}`", delete_after=5)

        elif command == "상메노래" or command == "listening":
            await message.delete()
            status_text = args.strip()
            if not status_text:
                await message.channel.send(f"> **[오류]**: 노래 상태를 입력하세요. 예: `{prefix}상메노래 음악 듣는 중`", delete_after=5)
                return
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status_text))
            await message.channel.send(f"> 노래 상태를 `{status_text}`로 설정했습니다.", delete_after=5)

        elif command == "상메영상" or command == "watching":
            await message.delete()
            status_text = args.strip()
            if not status_text:
                await message.channel.send(f"> **[오류]**: 영상 상태를 입력하세요. 예: `{prefix}상메영상 영화 보는 중`", delete_after=5)
                return
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
            await message.channel.send(f"> 영상 상태를 `{status_text}`로 설정했습니다.", delete_after=5)

        elif command == "상메삭제" or command == "stopactivity" or command == "stopstreaming" or command == "stopstatus" or command == "stoplistening" or command == "stopplaying" or command == "stopwatching":
            await message.delete()
            await client.change_presence(activity=None)
            await message.channel.send(f"> 상태 메시지를 삭제했습니다.", delete_after=5)

        elif command == "상태변경":
            await message.delete()
            status_text = args.strip()
            status_map = {
                "온라인": discord.Status.online,
                "자리비움": discord.Status.idle,
                "다른용무중": discord.Status.dnd,
                "오프라인": discord.Status.offline
            }
            if not status_text or status_text not in status_map:
                await message.channel.send(f"> **[오류]**: 상태는 '온라인', '자리비움', '다른용무중', '오프라인' 중 하나여야 합니다.", delete_after=5)
                return
            await client.change_presence(status=status_map[status_text])
            await message.channel.send(f"> 상태를 `{status_text}`로 변경했습니다.", delete_after=5)

        elif command == "계좌설정":
            await message.delete()
            parts = args.split(' ', 2)
            if len(parts) < 3:
                await message.channel.send(f"> **[오류]**: 은행, 계좌번호, 예금주를 입력하세요. 예: `{prefix}계좌설정 국민은행 123-456-789 김민준`", delete_after=5)
                return
            bank, account_number, account_holder = parts[0], parts[1], parts[2]
            config["account_info"] = {"bank": bank, "account_number": account_number, "account_holder": account_holder}
            save_config(config)
            await message.channel.send(f"> 계좌 정보 설정 완료: `{bank} {account_number} ({account_holder})`", delete_after=5)

        elif command == "계좌":
            await message.delete()
            account = config.get("account_info", {})
            if not account.get("bank"):
                await message.channel.send(f"> **[오류]**: 계좌 정보가 설정되지 않았습니다.", delete_after=5)
                return
            await message.channel.send(f"> **계좌 정보**\n> 은행: `{account['bank']}`\n> 계좌번호: `{account['account_number']}`\n> 예금주: `{account['account_holder']}`", delete_after=5)

        elif command == "계좌삭제":
            await message.delete()
            if "account_info" in config:
                del config["account_info"]
                save_config(config)
            await message.channel.send(f"> 계좌 정보가 삭제되었습니다.", delete_after=5)

        elif command == "남은기간":
            await message.delete()
            await message.channel.send(f"> **[오류]**: 라이센스 시스템이 구현되지 않았습니다.", delete_after=5)

        elif command == "유저파싱" or command == "usericon" or command == "uicon":
            await message.delete()
            user_obj = None
            if message.mentions:
                user_obj = message.mentions[0]
            elif args.isdigit():
                try:
                    user_obj = await client.fetch_user(int(args))
                except discord.NotFound:
                    pass

            if not user_obj:
                await message.channel.send(f"> **[오류]**: 유저 ID를 입력하거나 유저를 멘션하세요. 예: `{prefix}유저파싱 123456789` 또는 `{prefix}usericon @유저`", delete_after=5)
                return
            try:
                avatar_url = user_obj.avatar.url if user_obj.avatar else user_obj.default_avatar.url
                await message.channel.send(f"> **유저 정보**\n> 이름: `{user_obj.name}`\n> ID: `{user_obj.id}`\n> 아바타: `{avatar_url}`", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 유저 정보 조회 실패: `{str(e)}`", delete_after=5)

        elif command == "서버정보" or command == "guildinfo" or command == "ginfo":
            await message.delete()
            guild_obj = message.guild
            if args:
                try:
                    guild_id = int(args)
                    guild_obj = client.get_guild(guild_id)
                    if not guild_obj:
                        guild_obj = await client.fetch_guild(guild_id)
                except (ValueError, discord.NotFound, discord.Forbidden):
                    await message.channel.send(f"> **[오류]**: 유효한 서버 ID를 입력하거나 서버에서 명령어를 사용하세요.", delete_after=5)
                    return
                except Exception as e:
                    await message.channel.send(f"> **[오류]**: 서버 정보 조회 실패: `{str(e)}`", delete_after=5)
                    return

            if not guild_obj:
                await message.channel.send("> **[오류]**: 이 명령은 서버에서만 사용 가능합니다.", delete_after=5)
                return

            date_format = "%Y-%m-%d %H:%M:%S"
            embed_desc = f"""> **서버 정보 | 접두사: `{prefix}`**
:dividers: __기본 정보__
서버 이름: `{guild_obj.name}`
서버 ID: `{guild_obj.id}`
생성일: `{guild_obj.created_at.strftime(date_format)}`
서버 아이콘: `{guild_obj.icon.url if guild_obj.icon else '없음'}`
서버 소유자: `{guild_obj.owner}`
:page_facing_up: __기타 정보__
`{len(guild_obj.members)}` 멤버
`{len(guild_obj.roles)}` 역할
`{len(guild_obj.text_channels) if guild_obj.text_channels else '없음'}` 텍스트 채널
`{len(guild_obj.voice_channels) if guild_obj.voice_channels else '없음'}` 음성 채널
`{len(guild_obj.categories) if guild_obj.categories else '없음'}` 카테고리"""
            embed = discord.Embed(description=embed_desc, color=0x00ff00)
            await message.channel.send(embed=embed, delete_after=30)

        elif command == "접속기기":
            await message.delete()
            await message.channel.send(f"> **[오류]**: 접속 기기 정보는 API로 확인할 수 없습니다.", delete_after=5)

        elif command == "할말":
            await message.delete()
            msg_content = args.strip()
            if not msg_content:
                await message.channel.send(f"> **[오류]**: 메시지를 입력하세요. 예: `{prefix}할말 안녕하세요`", delete_after=5)
                return
            embed = discord.Embed(description=msg_content, color=0x00ff00)
            await message.channel.send(embed=embed)

        elif command == "채널리셋":
            await message.delete()
            try:
                channel_id = int(args)
            except ValueError:
                channel_id = None
            if not channel_id:
                await message.channel.send(f"> **[오류]**: 채널 ID를 입력하세요. 예: `{prefix}채널리셋 123456789`", delete_after=5)
                return
            channel = client.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                await message.channel.send(f"> **[오류]**: 유효한 텍스트 채널 ID를 입력하세요.", delete_after=5)
                return
            if not message.guild.me.guild_permissions.manage_channels:
                await message.channel.send(f"> **[오류]**: 채널 관리 권한이 없습니다.", delete_after=5)
                return
            try:
                new_channel = await channel.clone(name=channel.name)
                await channel.delete()
                await new_channel.send(f"채널 `{new_channel.name}`이 재생성되었습니다.")
                await message.channel.send(f"> 채널 `{new_channel.name}`이 재생성되었습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 채널 재생성 실패: `{str(e)}`", delete_after=5)

        elif command == "첫메시지" or command == "firstmessage":
            await message.delete()
            try:
                messages_fetched = [msg async for msg in message.channel.history(limit=1, oldest_first=True)]
                if messages_fetched:
                    first_message = messages_fetched[0]
                    link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{first_message.id}"
                    await message.channel.send(f"> 첫 메시지 링크: `{link}`", delete_after=5)
                else:
                    await message.channel.send(f"> **[오류]**: 채널에 메시지가 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 첫 메시지 조회 실패: `{str(e)}`", delete_after=5)

        elif command == "검색":
            await message.delete()
            query = args.strip()
            if not query:
                await message.channel.send(f"> **[오류]**: 검색어를 입력하세요. 예: `{prefix}검색 디스코드`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 검색 API가 구현되지 않았습니다. 검색어: `{query}`", delete_after=5)

        elif command == "유튜브":
            await message.delete()
            query = args.strip()
            if not query:
                await message.channel.send(f"> **[오류]**: 검색어를 입력하세요. 예: `{prefix}유튜브 강아지`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 유튜브 API가 구현되지 않았습니다. 검색어: `{query}`", delete_after=5)

        elif command == "노래가사":
            await message.delete()
            title = args.strip()
            if not title:
                await message.channel.send(f"> **[오류]**: 노래 제목을 입력하세요. 예: `{prefix}노래가사 Happy`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 가사 검색 API가 구현되지 않았습니다. 제목: `{title}`", delete_after=5)

        elif command == "스크린샷":
            await message.delete()
            url = args.strip()
            if not url:
                await message.channel.send(f"> **[오류]**: URL을 입력하세요. 예: `{prefix}스크린샷 https://example.com`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 스크린샷 API가 구현되지 않았습니다. URL: `{url}`", delete_after=5)

        elif command == "하이퍼스쿼드" or command == "hypesquad" or command == "hs":
            await message.delete()
            squad = args.strip()
            if not squad:
                await message.channel.send(f"> **[오류]**: 스쿼드를 입력하세요. 예: `{prefix}하이퍼스쿼드 Bravery`", delete_after=5)
                return
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            payload = {}
            if squad.lower() == "bravery":
                payload = {'house_id': 1}
            elif squad.lower() == "brilliance":
                payload = {'house_id': 2}
            elif squad.lower() == "balance":
                payload = {'house_id': 3}
            else:
                await message.channel.send(f"> **[오류]**: 스쿼드는 'Bravery', 'Brilliance', 'Balance' 중 하나여야 합니다.", delete_after=5)
                return
            try:
                r = requests.post('https://discordapp.com/api/v6/hypesquad/online', headers=headers, json=payload, timeout=10)
                r.raise_for_status()
                await message.channel.send(f"> 하이퍼스쿼드가 `{squad}`로 변경되었습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 하이퍼스쿼드 변경 실패: `{str(e)}`", delete_after=5)

        elif command == "하이퍼스쿼드목록":
            await message.delete()
            await message.channel.send(f"> **하이퍼스쿼드 목록**\n> - Bravery\n> - Brilliance\n> - Balance", delete_after=5)

        elif command == "guildicon" or command == "gicon":
            await message.delete()
            if not message.guild:
                await message.channel.send("> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.", delete_after=5)
                return
            await message.channel.send(f"> **{message.guild.name} 아이콘 :**\n{message.guild.icon.url if message.guild.icon else '*아이콘 없음*'}", delete_after=30)

        elif command == "guildbanner" or command == "gbanner":
            await message.delete()
            if not message.guild:
                await message.channel.send("> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.", delete_after=5)
                return
            await message.channel.send(f"> **{message.guild.name} 배너 :**\n{message.guild.banner.url if message.guild.banner else '*배너 없음*'}", delete_after=30)

        elif command == "ascii":
            await message.delete()
            if not args:
                await message.channel.send(f"> **[오류]**: 잘못된 명령어.\n> __명령어__: `ascii <메시지>`", delete_after=5)
                return
            try:
                ascii_art_output = pyfiglet.figlet_format(args)
                if len(f"\`\`\`\n{ascii_art_output}\n\`\`\`") > 2000:
                    await message.channel.send("> **[오류]**: ASCII 아트가 너무 커서 보낼 수 없습니다.", delete_after=5)
                    return
                await message.channel.send(f"\`\`\`\n{ascii_art_output}\n\`\`\`", delete_after=30)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: ASCII 아트 생성 중 오류가 발생했습니다. `{e}`", delete_after=5)

        elif command == "코인지갑설정":
            await message.delete()
            address = args.strip()
            if not address:
                await message.channel.send(f"> **[오류]**: 지갑 주소를 입력하세요. 예: `{prefix}코인지갑설정 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`", delete_after=5)
                return
            config["coin_wallet"]["address"] = address
            save_config(config)
            await message.channel.send(f"> 코인 지갑 주소가 `{address}`로 설정되었습니다.", delete_after=5)

        elif command == "코인지갑":
            await message.delete()
            address = config.get("coin_wallet", {}).get("address", "")
            if not address:
                await message.channel.send(f"> **[오류]**: 코인 지갑 주소가 설정되지 않았습니다.", delete_after=5)
                return
            await message.channel.send(f"> **코인 지갑 주소**: `{address}`", delete_after=5)

        elif command == "코인잔액":
            await message.delete()
            parts = args.split(' ', 1)
            coin = parts[0].upper() if parts else None
            address = parts[1] if len(parts) > 1 else config.get("coin_wallet", {}).get("address", "")
            if not coin:
                await message.channel.send(f"> **[오류]**: 코인 종류를 입력하세요 (BTC, LTC, DOGE, DASH, BCH). 예: `{prefix}코인잔액 BTC`", delete_after=5)
                return
            if not address:
                await message.channel.send(f"> **[오류]**: 지갑 주소를 입력하거나 먼저 설정하세요.", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 코인 잔액 조회 API    구현되지 않았습니다. 코인: `{coin}`, 주소: `{address}`", delete_after=5)

        elif command == "메세지전부보내기" or command == "sendall":
            await message.delete()
            parts = args.rsplit(" ", 1)
            msg_content = "https://discord.gg/PKR7nM9j9U"
            delay = 0.5
            if len(parts) > 1 and parts[1].replace('.', '', 1).isdigit():
                msg_content = parts[0]
                try:
                    delay = float(parts[1])
                except ValueError:
                    pass
            elif args:
                msg_content = args

            if not message.guild:
                await message.channel.send(f"> **[오류]**: 서버에서만 사용 가능합니다.", delete_after=5)
                return
            channels = message.guild.text_channels
            task_key = f"send_all_messages_{message.guild.id}_{message.channel.id}"
            spam_tasks[task_key] = True
            success_count = 0
            failure_count = 0
            await message.channel.send(f"> {len(channels)}개 채널로 메시지 방송을 시작합니다...", delete_after=5)
            for channel in channels:
                if not spam_tasks.get(task_key):
                    break
                try:
                    await channel.send(msg_content)
                    success_count += 1
                    await asyncio.sleep(delay)
                except Exception:
                    failure_count += 1
            if task_key in spam_tasks:
                del spam_tasks[task_key]
            await message.channel.send(f"> 전송 완료: 성공 `{success_count}`, 실패 `{failure_count}`", delete_after=5)

        elif command == "메세지전부보내기중단":
            await message.delete()
            task_key = f"send_all_messages_{message.guild.id}_{message.channel.id}"
            if task_key in spam_tasks:
                del spam_tasks[task_key]
                await message.channel.send(f"> 메시지 전송이 중단되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 진행 중인 전송이 없습니다.", delete_after=5)

        elif command == "도배" or command == "spam":
            await message.delete()
            msg_content = config.get("spam_message", "기본 도배 메시지")
            delay = config.get("delay", 1000) / 1000
            count = config.get("spam_count", 5)

            if " | " in args:
                parts = args.rsplit(" | ", 1)
                msg_content = parts[0]
                try:
                    delay = float(parts[1])
                except ValueError:
                    await message.channel.send(f"> **[오류]**: 메시지와 딜레이를 입력하세요. 예: `{prefix}도배 안녕하세요 | 5`", delete_after=5)
                    return
            elif args:
                msg_content = args

            if count > 9:
                await message.channel.send(f"> **[오류]**: 도배 횟수는 최대 9입니다.", delete_after=5)
                return
            
            task_key = f"spam_task_{message.channel.id}"
            spam_tasks[task_key] = True
            try:
                for _ in range(count):
                    if not spam_tasks.get(task_key):
                        break
                    await message.channel.send(msg_content)
                    await asyncio.sleep(delay)
                if task_key in spam_tasks:
                    del spam_tasks[task_key]
                    await message.channel.send(f"> 도배 완료: `{count}`회 전송", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 도배 중 오류: `{str(e)}`", delete_after=5)

        elif command == "도배중단":
            await message.delete()
            task_key = f"spam_task_{message.channel.id}"
            if task_key in spam_tasks:
                del spam_tasks[task_key]
                await message.channel.send(f"> 도배가 중단되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 진행 중인 도배가 없습니다.", delete_after=5)

        elif command == "전체멘션":
            await message.delete()
            if not message.guild:
                await message.channel.send(f"> **[오류]**: 서버에서만 사용 가능합니다.", delete_after=5)
                return
            members = [m.mention for m in message.guild.members if not m.bot]
            mentions_str = " ".join(members)
            if len(mentions_str) > 2000:
                await message.channel.send(f"> **[오류]**: 멘션할 멤버가 너무 많습니다. 메시지 제한을 초과합니다.", delete_after=5)
                return
            await message.channel.send(mentions_str, delete_after=5)

        elif command == "권모술수1":
            await message.delete()
            words = config.get("words", [])
            
            delay = config.get("delay", 1000) / 1000 # Use default delay from config

            if not words:
                await message.channel.send(f"> **[오류]**: 단어 목록이 비어 있습니다. config.json에서 단어를 추가하세요.", delete_after=5)
                return
            
            task_key = f"random_spam_task_1_{message.channel.id}"
            if spam_tasks.get(task_key): # Check if already running
                await message.channel.send(f"> **[오류]**: 권모술수1이 이미 이 채널에서 실행 중입니다. 중지하려면 `{prefix}권모술수중지`를 사용하세요.", delete_after=5)
                return

            spam_tasks[task_key] = True
            try:
                await message.channel.send(f"> 권모술수1 시작: 취소할 때까지 전송합니다. (간격: `{delay}`초)", delete_after=5)
                while spam_tasks.get(task_key): # Continuous loop
                    result = ''.join(random.choice(words) for _ in range(random.randint(5, 15)))
                    await message.channel.send(result)
                    await asyncio.sleep(delay)
                # This part will only be reached if spam_tasks[task_key] becomes False (i.e., stopped by another command)
                await message.channel.send(f"> 권모술수1이 중단되었습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 권모술수1 중 오류: `{str(e)}`", delete_after=5)
                if task_key in spam_tasks: # Ensure task is removed on error
                    del spam_tasks[task_key]

        elif command == "권모술수2":
            await message.delete()
            words = config.get("words", [])
            
            delay = config.get("delay", 1000) / 1000 # Use default delay from config

            if not words:
                await message.channel.send(f"> **[오류]**: 단어 목록이 비어 있습니다. config.json에서 단어를 추가하세요.", delete_after=5)
                return
            
            task_key = f"random_spam_task_2_{message.channel.id}"
            if spam_tasks.get(task_key): # Check if already running
                await message.channel.send(f"> **[오류]**: 권모술수2가 이미 이 채널에서 실행 중입니다. 중지하려면 `{prefix}권모술수중지`를 사용하세요.", delete_after=5)
                return

            spam_tasks[task_key] = True
            try:
                await message.channel.send(f"> 권모술수2 시작: 취소할 때까지 전송합니다. (간격: `{delay}`초)", delete_after=5)
                while spam_tasks.get(task_key): # Continuous loop
                    result = ' '.join(random.choice(words) for _ in range(random.randint(5, 15)))
                    await message.channel.send(result)
                    await asyncio.sleep(delay)
                # This part will only be reached if spam_tasks[task_key] becomes False
                await message.channel.send(f"> 권모술수2가 중단되었습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 권모술수2 중 오류: `{str(e)}`", delete_after=5)
                if task_key in spam_tasks: # Ensure task is removed on error
                    del spam_tasks[task_key]

        elif command == "권모술수중지":
            await message.delete()
            stopped_any = False
            task_key_1 = f"random_spam_task_1_{message.channel.id}"
            task_key_2 = f"random_spam_task_2_{message.channel.id}"

            if task_key_1 in spam_tasks:
                del spam_tasks[task_key_1]
                stopped_any = True
            if task_key_2 in spam_tasks:
                del spam_tasks[task_key_2]
                stopped_any = True
            
            if stopped_any:
                await message.channel.send(f"> 권모술수가 중단되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 진행 중인 권모술수가 없습니다.", delete_after=5)

        elif command == "dmall":
            await message.delete()
            msg_content = args if args else "https://discord.gg/PKR7nM9j9U"

            if not message.guild:
                await message.channel.send("> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.", delete_after=5)
                return

            members = [m for m in message.guild.members if not m.bot]
            total_members = len(members)
            estimated_time = round(total_members * 4.5)

            await message.channel.send(f"> `{total_members}`명의 멤버에게 DM 전송을 시작합니다.\n> 예상 시간: `{estimated_time}초` (~{round(estimated_time / 60, 2)}분)", delete_after=10)

            success_count = 0
            fail_count = 0

            for member in members:
                try:
                    await member.send(msg_content)
                    success_count += 1
                except Exception:
                    fail_count += 1
                await asyncio.sleep(random.uniform(3, 6))

            await message.channel.send(f"> **[정보]**: DM 전송이 완료되었습니다.\n> 성공: `{success_count}`\n> 실패: `{fail_count}`", delete_after=10)

        elif command == "아이피조회" or command == "geoip":
            await message.delete()
            ip = args.strip()
            if not ip:
                await message.channel.send(f"> **[오류]**: IP 주소를 입력하세요. 예: `{prefix}아이피조회 8.8.8.8`", delete_after=5)
                return
            try:
                r = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
                r.raise_for_status()
                geo = r.json()
                if geo['status'] == 'fail':
                    await message.channel.send(f"> **[오류]**: 유효하지 않은 IP 주소입니다.", delete_after=5)
                    return
                embed_desc = f"""
> **IP 조회 결과**
> IP: `{geo.get('query', 'N/A')}`
> 국가-지역: `{geo.get('country', 'N/A')} - {geo.get('regionName', 'N/A')}`
> 도시: `{geo.get('city', 'N/A')} ({geo.get('zip', 'N/A')})`
> 위도-경도: `{geo.get('lat', 'N/A')} - {geo.get('lon', 'N/A')}`
> ISP: `{geo.get('isp', 'N/A')}`
> 조직: `{geo.get('org', 'N/A')}`
> 시간대: `{geo.get('timezone', 'N/A')}`
> AS: `{geo.get('as', 'N/A')}`
"""
                embed = discord.Embed(description=embed_desc, color=0x00ff00)
                await message.channel.send(embed=embed, delete_after=5)
            except requests.exceptions.RequestException as e:
                await message.channel.send(f"> **[오류]**: IP 조회 실패 (HTTP 요청 오류): `{str(e)}`", delete_after=5)
            except json.JSONDecodeError:
                await message.channel.send(f"> **[오류]**: IP 조회 실패 (응답 파싱 오류).", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: IP 조회 실패: `{str(e)}`", delete_after=5)

        elif command == "토큰조회" or command == "tokeninfo" or command == "tinfo":
            await message.delete()
            token_to_check = args.strip()
            if not token_to_check:
                await message.channel.send(f"> **[오류]**: 토큰을 입력하세요. 예: `{prefix}토큰조회 <토큰>`", delete_after=5)
                return
            headers = {'Authorization': token_to_check, 'Content-Type': 'application/json'}
            languages = {
                'da': '덴마크어, 덴마크', 'de': '독일어, 독일', 'en-GB': '영어, 영국',
                'en-US': '영어, 미국', 'es-ES': '스페인어, 스페인', 'fr': '프랑스어, 프랑스',
                'hr': '크로아티아어, 크로아티아', 'lt': '리투아니아어, 리투아니아', 'hu': '헝가리어, 헝가리',
                'nl': '네덜란드어, 네덜란드', 'no': '노르웨이어, 노르웨이', 'pl': '폴란드어, 폴란드',
                'pt-BR': '포르투갈어, 브라질', 'ro': '루마니아어, 루마니아', 'fi': '핀란드어, 핀란드',
                'sv-SE': '스웨덴어, 스웨덴', 'vi': '베트남어, 베트남', 'tr': '터키어, 터키',
                'cs': '체코어, 체코', 'el': '그리스어, 그리스', 'bg': '불가리아어, 불가리아',
                'ru': '러시아어, 러시아', 'uk': '우크라이나어, 우크라이나', 'th': '태국어, 태국',
                'zh-CN': '중국어, 중국', 'ja': '일본어', 'zh-TW': '중국어, 대만', 'ko': '한국어, 한국'
            }
            try:
                res = requests.get('https://discordapp.com/api/v6/users/@me', headers=headers, timeout=5)
                res.raise_for_status()
                data = res.json()
                user_name = f'{data.get("username", "N/A")}#{data.get("discriminator", "N/A")}'
                user_id = data.get('id', 'N/A')
                avatar_id = data.get('avatar')
                avatar_url = f'https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.gif' if avatar_id else '없음'
                phone_number = data.get('phone', '없음')
                email = data.get('email', '없음')
                mfa_enabled = data.get('mfa_enabled', 'N/A')
                flags = data.get('flags', 'N/A')
                locale = data.get('locale', 'N/A')
                verified = data.get('verified', 'N/A')
                days_left = "없음"
                language = languages.get(locale, '알 수 없음')
                creation_date = datetime.datetime.fromtimestamp(((int(user_id) >> 22) + 1420070400000) / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
                has_nitro = False

                try:
                    nitro_res = requests.get('https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers=headers, timeout=5)
                    nitro_res.raise_for_status()
                    nitro_data = nitro_res.json()
                    has_nitro = bool(len(nitro_data) > 0)
                    if has_nitro:
                        d1 = datetime.datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        d2 = datetime.datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        days_left = abs((d2 - d1).days)
                except requests.exceptions.RequestException:
                    pass

                embed_desc = f"""**토큰 정보 | 접두사: `{prefix}`**

        > :dividers: __기본 정보__
	사용자 이름: `{user_name}`
	사용자 ID: `{user_id}`
	생성일: `{creation_date}`
	아바타 URL: `{avatar_url}`
        > :crystal_ball: __니트로 정보__
	니트로 상태: `{has_nitro}`
	만료까지: `{days_left}일`
        > :incoming_envelope: __연락처 정보__
	전화번호: `{phone_number}`
	이메일: `{email}`
        > :shield: __계정 보안__
	2FA/MFA 활성화: `{mfa_enabled}`
	플래그: `{flags}`
        > :paperclip: __기타__
	지역: `{locale} ({language})`
	이메일 인증됨: `{verified}`"""

                embed = discord.Embed(description=embed_desc, color=0x00ff00)
                await message.channel.send(embed=embed, delete_after=30)
            except requests.exceptions.RequestException as e:
                await message.channel.send(f"> **[오류]**: 토큰 조회 실패 (HTTP 요청 오류): `{str(e)}`", delete_after=5)
            except json.JSONDecodeError:
                await message.channel.send(f"> **[오류]**: 토큰 조회 실패 (응답 파싱 오류).", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 토큰 조회 실패: `{str(e)}`", delete_after=5)

        elif command == "토큰확인":
            await message.delete()
            token_to_check = args.strip()
            if not token_to_check:
                await message.channel.send(f"> **[오류]**: 토큰을 입력하세요. 예: `{prefix}토큰확인 <토큰>`", delete_after=5)
                return
            headers = {'Authorization': token_to_check, 'Content-Type': 'application/json'}
            try:
                res = requests.get('https://discordapp.com/api/v6/users/@me', headers=headers, timeout=5)
                if res.status_code == 200:
                    await message.channel.send(f"> 토큰 유효: `{token_to_check[:10]}...`", delete_after=5)
                else:
                    await message.channel.send(f"> **[오류]**: 유효하지 않은 토큰입니다. 상태 코드: `{res.status_code}`", delete_after=5)
            except requests.exceptions.RequestException as e:
                await message.channel.send(f"> **[오류]**: 토큰 확인 실패 (HTTP 요청 오류): `{str(e)}`", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 토큰 확인 실패: `{str(e)}`", delete_after=5)

        elif command == "택배조회":
            await message.delete()
            parts = args.split(' ', 1)
            carrier = parts[0] if parts else None
            tracking_number = parts[1] if len(parts) > 1 else None
            if not carrier or not tracking_number:
                await message.channel.send(f"> **[오류]**: 택배사와 운송장 번호를 입력하세요. 예: `{prefix}택배조회 CJ대한통운 123456789`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 택배 조회 API가 구현되지 않았습니다. 택배사: `{carrier}`, 운송장: `{tracking_number}`", delete_after=5)

        elif command == "로블쿠키":
            await message.delete()
            cookie = args.strip()
            if not cookie:
                await message.channel.send(f"> **[오류]**: 로블록스 쿠키를 입력하세요. 예: `{prefix}로블쿠키 <쿠키>`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 로블록스 API가 구현되지 않았습니다. 쿠키: `{cookie[:10]}...`", delete_after=5)

        elif command == "마크서버":
            await message.delete()
            server_address = args.strip()
            if not server_address:
                await message.channel.send(f"> **[오류]**: 서버 주소를 입력하세요. 예: `{prefix}마크서버 play.hypixel.net`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 마인크래프트 서버 조회 API가 구현되지 않았습니다. 주소: `{server_address}`", delete_after=5)

        elif command == "인스타":
            await message.delete()
            instagram_id = args.strip()
            if not instagram_id:
                await message.channel.send(f"> **[오류]**: 인스타그램 ID를 입력하세요. 예: `{prefix}인스타 example`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 인스타그램 API가 구현되지 않았습니다. ID: `{instagram_id}`", delete_after=5)

        elif command == "파트너지정":
            await message.delete()
            try:
                channel_id = int(args)
            except ValueError:
                channel_id = None
            if not channel_id:
                await message.channel.send(f"> **[오류]**: 채널 ID를 입력하세요. 예: `{prefix}파트너지정 123456789`", delete_after=5)
                return
            if channel_id not in config["partner_channels"]:
                config["partner_channels"].append(channel_id)
                save_config(config)
                await message.channel.send(f"> 채널 `{channel_id}`가 파트너 채널로 지정되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 이미 파트너 채널로 지정되어 있습니다.", delete_after=5)

        elif command == "파트너삭제":
            await message.delete()
            try:
                channel_id = int(args)
            except ValueError:
                channel_id = None
            if not channel_id:
                await message.channel.send(f"> **[오류]**: 채널 ID를 입력하세요. 예: `{prefix}파트너삭제 123456789`", delete_after=5)
                return
            if channel_id in config["partner_channels"]:
                config["partner_channels"].remove(channel_id)
                save_config(config)
                await message.channel.send(f"> 채널 `{channel_id}`가 파트너 채널에서 삭제되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 파트너 채널에 존재하지 않습니다.", delete_after=5)

        elif command == "파트너목록":
            await message.delete()
            if not config["partner_channels"]:
                await message.channel.send(f"> 파트너 채널이 없습니다.", delete_after=5)
                return
            await message.channel.send(f"> **파트너 채널 목록**\n> " + "\n> ".join(str(c) for c in config["partner_channels"]), delete_after=5)

        elif command == "파트너메세지":
            await message.delete()
            msg_content = args.strip()
            if not msg_content:
                await message.channel.send(f"> **[오류]**: 메시지를 입력하세요. 예: `{prefix}파트너메세지 안녕하세요`", delete_after=5)
                return
            success_count = 0
            failure_count = 0
            for channel_id in config["partner_channels"]:
                channel = client.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(msg_content)
                        success_count += 1
                    except Exception:
                        failure_count += 1
                else:
                    failure_count += 1
            await message.channel.send(f"> 전송 완료: 성공 `{success_count}`, 실패 `{failure_count}`", delete_after=5)

        elif command == "예약":
            await message.delete()
            parts = args.split(' ', 3)
            if len(parts) < 3:
                await message.channel.send(f"> **[오류]**: 채널, 시간, 메시지를 입력하세요. 예: `{prefix}예약 #채널 14:30 매일 안녕하세요`", delete_after=5)
                return
            
            channel_mention = parts[0]
            time_str = parts[1]
            repeat = parts[2] if len(parts) > 2 else None
            msg_content = parts[3] if len(parts) > 3 else ""

            channel = None
            if message.channel_mentions:
                channel = message.channel_mentions[0]
            elif channel_mention.isdigit():
                channel = client.get_channel(int(channel_mention))

            if not channel:
                await message.channel.send(f"> **[오류]**: 유효한 채널을 멘션하거나 ID를 입력하세요.", delete_after=5)
                return

            try:
                datetime.datetime.strptime(time_str, "%H:%M")
                schedule_id = len(config["scheduled_messages"]) + 1
                config["scheduled_messages"].append({
                    "id": schedule_id,
                    "channel_id": channel.id,
                    "time": time_str,
                    "repeat": repeat,
                    "message": msg_content
                })
                save_config(config)
                await message.channel.send(f"> 메시지 예약 완료: `{channel.name}`에 `{time_str}` `{msg_content}` (ID: {schedule_id})", delete_after=5)
            except ValueError:
                await message.channel.send(f"> **[오류]**: 올바른 시간 형식을 입력하세요 (HH:MM).", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 예약 설정 실패: `{str(e)}`", delete_after=5)

        elif command == "예약목록":
            await message.delete()
            if not config["scheduled_messages"]:
                await message.channel.send(f"> 예약된 메시지가 없습니다.", delete_after=5)
                return
            messages_list = "\n".join(f"> ID `{m['id']}`: 채널 `{client.get_channel(int(m['channel_id'])).name if client.get_channel(int(m['channel_id'])) else m['channel_id']}`, 시간 `{m['time']}`, 반복 `{m['repeat'] or '없음'}`, 메시지 `{m['message']}`" for m in config["scheduled_messages"])
            await message.channel.send(f"> **예약 목록**\n{messages_list}", delete_after=5)

        elif command == "예약취소":
            await message.delete()
            try:
                schedule_id = int(args)
            except ValueError:
                schedule_id = None
            if not schedule_id:
                await message.channel.send(f"> **[오류]**: 예약 ID를 입력하세요. 예: `{prefix}예약취소 1`", delete_after=5)
                return
            
            initial_len = len(config["scheduled_messages"])
            config["scheduled_messages"] = [msg for msg in config["scheduled_messages"] if msg["id"] != schedule_id]
            
            if len(config["scheduled_messages"]) < initial_len:
                save_config(config)
                await message.channel.send(f"> 예약 ID `{schedule_id}`가 취소되었습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 예약 ID `{schedule_id}`를 찾을 수 없습니다.", delete_after=5)

        elif command == "멘션테러":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2 or not parts[0].isdigit() or not message.mentions:
                await message.channel.send(f"> **[오류]**: 횟수와 유저를 멘션하세요. 예: `{prefix}멘션테러 5 @유저`", delete_after=5)
                return
            count = int(parts[0])
            user_to_mention = message.mentions[0]
            if count > 10:
                await message.channel.send(f"> **[오류]**: 횟수는 최대 10입니다.", delete_after=5)
                return
            try:
                for i in range(count):
                    await message.channel.send(f"{user_to_mention.mention} (테러 {i+1}/{count})")
                    await asyncio.sleep(1)
                await message.channel.send(f"> 멘션 테러 완료: `{user_to_mention.name}`을 `{count}`회 멘션", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 멘션 테러 실패: `{str(e)}`", delete_after=5)

        elif command == "잠수" or command == "afk":
            await message.delete()
            msg_content = args.strip()
            if not msg_content:
                await message.channel.send(f"> **[오류]**: 메시지를 입력하세요. 예: `{prefix}잠수 잠수 중입니다`", delete_after=5)
                return
            config["잠수"]["enabled"] = True
            config["잠수"]["message"] = msg_content
            save_config(config)
            await message.channel.send(f"> 잠수 상태 설정: `{msg_content}`", delete_after=5)

        elif command == "잠수해제":
            await message.delete()
            if not config["잠수"]["enabled"]:
                await message.channel.send(f"> **[오류]**: 잠수 상태가 설정되지 않았습니다.", delete_after=5)
                return
            config["잠수"]["enabled"] = False
            save_config(config)
            await message.channel.send(f"> 잠수 상태가 해제되었습니다.", delete_after=5)

        elif command == "이모지추가":
            await message.delete()
            parts = args.split(' ', 2)
            if len(parts) < 3 or not parts[0].isdigit() or not parts[1].isdigit():
                await message.channel.send(f"> **[오류]**: 유저 ID, 서버 ID, 이모지를 입력하세요. 예: `{prefix}이모지추가 123456789 987654321 😊`", delete_after=5)
                return
            user_id = int(parts[0])
            guild_id = int(parts[1])
            emoji = parts[2]
            config.setdefault("emoji_reactions", {}).setdefault(str(user_id), []).append({"guild_id": guild_id, "emoji": emoji})
            save_config(config)
            await message.channel.send(f"> 자동 이모지 반응 설정: 유저 `{user_id}`, 이모지 `{emoji}`", delete_after=5)

        elif command == "이모지삭제":
            await message.delete()
            parts = args.split(' ', 2)
            if len(parts) < 3 or not parts[0].isdigit() or not parts[1].isdigit():
                await message.channel.send(f"> **[오류]**: 유저 ID, 서버 ID, 이모지를 입력하세요. 예: `{prefix}이모지삭제 123456789 987654321 😊`", delete_after=5)
                return
            user_id = int(parts[0])
            guild_id = int(parts[1])
            emoji = parts[2]
            
            if str(user_id) in config.get("emoji_reactions", {}):
                initial_len = len(config["emoji_reactions"][str(user_id)])
                config["emoji_reactions"][str(user_id)] = [
                    e for e in config["emoji_reactions"][str(user_id)] 
                    if not (e["guild_id"] == guild_id and e["emoji"] == emoji)
                ]
                if len(config["emoji_reactions"][str(user_id)]) < initial_len:
                    save_config(config)
                    await message.channel.send(f"> 자동 이모지 반응 삭제: 유저 `{user_id}`, 이모지 `{emoji}`", delete_after=5)
                else:
                    await message.channel.send(f"> **[오류]**: 해당 설정이 없습니다.", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 해당 설정이 없습니다.", delete_after=5)

        elif command == "이모지확대":
            await message.delete()
            emoji_str = args.strip()
            if not emoji_str:
                await message.channel.send(f"> **[오류]**: 이모지를 입력하세요. 예: `{prefix}이모지확대 😊`", delete_after=5)
                return
            if emoji_str.startswith('<:') and emoji_str.endswith('>'):
                parts = emoji_str.split(':')
                if len(parts) == 3:
                    emoji_id = parts[2][:-1]
                    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
                    await message.channel.send(f">   모지 확대: {emoji_url}", delete_after=10)
                    return
            elif emoji_str.startswith('<a:') and emoji_str.endswith('>'):
                parts = emoji_str.split(':')
                if len(parts) == 3:
                    emoji_id = parts[2][:-1]
                    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif"
                    await message.channel.send(f"> 이모지 확대: {emoji_url}", delete_after=10)
                    return
            await message.channel.send(f"> **[오류]**: 일반 이모지 또는 유효한 사용자 지정 이모지 형식을 입력하세요. 이모지: `{emoji_str}`", delete_after=5)

        elif command == "이모지스틸":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2 or not parts[0].isdigit():
                await message.channel.send(f"> **[오류]**: 서버 ID와 이모지를 입력하세요. 예: `{prefix}이모지스틸 123456789 <이모지>`", delete_after=5)
                return
            guild_id = int(parts[0])
            emoji_name_id = parts[1]
            
            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send(f"> **[오류]**: 지정된 서버를 찾을 수 없습니다.", delete_after=5)
                return

            if not message.author.guild_permissions.manage_emojis:
                await message.channel.send(f"> **[오류]**: 이모지 관리 권한이 없습니다.", delete_after=5)
                return

            if emoji_name_id.startswith('<') and emoji_name_id.endswith('>'):
                animated = emoji_name_id.startswith('<a:')
                parts = emoji_name_id[2 if animated else 1:-1].split(':')
                if len(parts) == 2:
                    emoji_name = parts[0]
                    emoji_id = parts[1]
                    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"
                    
                    try:
                        response = requests.get(emoji_url)
                        response.raise_for_status()
                        emoji_bytes = response.content

                        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                        await message.channel.send(f"> 이모지 `{new_emoji.name}`를 스틸하여 서버에 추가했습니다.", delete_after=5)
                    except requests.exceptions.RequestException as e:
                        await message.channel.send(f"> **[오류]**: 이모지 다운로드 실패: `{str(e)}`", delete_after=5)
                    except discord.HTTPException as e:
                        await message.channel.send(f"> **[오류]**: 이모지 생성 실패 (Discord API 오류): `{e}`", delete_after=5)
                    except Exception as e:
                        await message.channel.send(f"> **[오류]**: 이모지 스틸 실패: `{str(e)}`", delete_after=5)
                else:
                    await message.channel.send(f"> **[오류]**: 유효한 사용자 지정 이모지 형식이 아닙니다. 예: `<:이모지이름:123456789>`", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 사용자 지정 이모지를 입력해야 합니다. (예: `<:이모지이름:ID>`)", delete_after=5)

        elif command == "tts":
            await message.delete()
            if not args:
                await message.channel.send("> **[오류]**: 잘못된 명령어.\n> __명령어__: `tts <메시지>`", delete_after=5)
                return
            content = args.strip()
            try:
                tts_obj = gTTS(text=content, lang="ko") # 한국어로 변경
                f = io.BytesIO()
                tts_obj.write_to_fp(f)
                f.seek(0)
                await message.channel.send(file=discord.File(f, f"{content[:10]}.wav"), delete_after=30)
            except Exception as e:
                await message.channel.send(f'> **[오류]**: 텍스트를 음성으로 변환하지 못했습니다: `{str(e)}`', delete_after=5)

        elif command == "qr" or command == "qrcode":
            await message.delete()
            text_for_qr = args if args else "https://discord.gg/PKR7nM9j9U"
            try:
                qr_img = qrcode.make(text_for_qr)
                img_byte_arr = io.BytesIO()
                qr_img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                await message.channel.send(file=discord.File(img_byte_arr, "qr_code.png"), delete_after=30)
            except Exception as e:
                await message.channel.send(f'> **[오류]**: QR 코드를 생성하지 못했습니다: `{str(e)}`', delete_after=5)

        elif command == "autoreply" or command == "autor":
            await message.delete()
            parts = args.split(' ', 1)
            action = parts[0].upper() if parts else None
            user_obj = message.mentions[0] if message.mentions else None

            if action not in ["ON", "OFF"]:
                await message.channel.send(f"> **[오류]**: 잘못된 동작. `ON` 또는 `OFF`를 사용하세요.\n> __명령어__: `autoreply ON|OFF [@유저]`", delete_after=5)
                return

            if action == "ON":
                if user_obj:
                    if str(user_obj.id) not in config["autoreply"]["users"]:
                        config["autoreply"]["users"].append(str(user_obj.id))
                        config["autoreply"]["enabled"] = True
                        save_config(config)
                        selfbot_menu(client)
                    await message.channel.send(f"> **유저 {user_obj.mention}에 대한 자동 답장이 활성화되었습니다.**", delete_after=5)
                else:
                    if str(message.channel.id) not in config["autoreply"]["channels"]:
                        config["autoreply"]["channels"].append(str(message.channel.id))
                        config["autoreply"]["enabled"] = True
                        save_config(config)
                        selfbot_menu(client)
                    await message.channel.send("> **이 채널에서 자동 답장이 활성화되었습니다.**", delete_after=5)
            elif action == "OFF":
                if user_obj:
                    if str(user_obj.id) in config["autoreply"]["users"]:
                        config["autoreply"]["users"].remove(str(user_obj.id)) # Fixed: user.id to user_obj.id
                        if not config["autoreply"]["users"] and not config["autoreply"]["channels"]:
                            config["autoreply"]["enabled"] = False
                        save_config(config)
                        selfbot_menu(client)
                    await message.channel.send(f"> **유저 {user_obj.mention}에 대한 자동 답장이 비활성화되었습니다.**", delete_after=5)
                else:
                    if str(message.channel.id) in config["autoreply"]["channels"]:
                        config["autoreply"]["channels"].remove(str(message.channel.id))
                        if not config["autoreply"]["users"] and not config["autoreply"]["channels"]:
                            config["autoreply"]["enabled"] = False
                        save_config(config)
                        selfbot_menu(client)
                    await message.channel.send("> **이 채널에서 자동 답장이 비활성화되었습니다.**", delete_after=5)

        elif command == "remoteuser" or command == "remote":
            await message.delete()
            parts = args.split(' ', 1)
            action = parts[0].upper() if parts else None
            users_mentions = message.mentions

            if not users_mentions:
                await message.channel.send("> **[오류]**: 잘못된 명령어.\n> __명령어__: `remoteuser ADD|REMOVE <@유저(들)>`", delete_after=5)
                return

            if action not in ["ADD", "REMOVE"]:
                await message.channel.send(f"> **[오류]**: 잘못된 동작. `ADD` 또는 `REMOVE`를 사용하세요.\n> __명령어__: `remoteuser ADD|REMOVE <@유저(들)>`", delete_after=5)
                return

            if action == "ADD":
                added_count = 0
                for user in users_mentions:
                    if str(user.id) not in config["remote-users"]:
                        config["remote-users"].append(str(user.id))
                        added_count += 1
                save_config(config)
                selfbot_menu(client)
                await message.channel.send(f"> **성공**: {added_count}명의 유저가 원격 유저에 추가되었습니다.", delete_after=5)
            elif action == "REMOVE":
                removed_count = 0
                for user in users_mentions:
                    if str(user.id) in config["remote-users"]:
                        config["remote-users"].remove(str(user.id))
                        removed_count += 1
                save_config(config)
                selfbot_menu(client)
                await message.channel.send(f"> **성공**: {removed_count}명의 유저가 원격 유저에서 제거되었습니다.", delete_after=5)

        elif command == "copycat" or command == "copycatuser" or command == "copyuser":
            await message.delete()
            parts = args.split(' ', 1)
            action = parts[0].upper() if parts else None
            user_obj = message.mentions[0] if message.mentions else None

            if action not in ["ON", "OFF"]:
                await message.channel.send(f"> **[오류]**: 잘못된 동작. `ON` 또는 `OFF`를 사용하세요.\n> __명령어__: `copycat ON|OFF <@유저>`", delete_after=5)
                return

            if not user_obj:
                await message.channel.send(f"> **[오류]**: 복사할 유저를 지정하세요.\n> __명령어__: `copycat ON|OFF <@유저>`", delete_after=5)
                return

            if action == "ON":
                if user_obj.id not in config['copycat']['users']:
                    config['copycat']['users'].append(user_obj.id)
                    config['copycat']['enabled'] = True
                    save_config(config)
                    await message.channel.send(f"> 이제 `{str(user_obj)}`를 복사합니다.", delete_after=5)
                else:
                    await message.channel.send(f"> `{str(user_obj)}`는 이미 복사 중입니다.", delete_after=5)

            elif action == "OFF":
                if user_obj.id in config['copycat']['users']:
                    config['copycat']['users'].remove(user_obj.id)
                    if not config['copycat']['users']:
                        config['copycat']['enabled'] = False
                    save_config(config)
                    await message.channel.send(f"> `{str(user_obj)}` 복사를 중지했습니다.", delete_after=5)
                else:
                    await message.channel.send(f"> `{str(user_obj)}`는 복사 중이 아니었습니다.", delete_after=5)

        elif command == "fetchmembers" or command == "fetch":
            await message.delete()
            if not message.guild:
                await message.channel.send(f'> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.', delete_after=5)
                return

            members = message.guild.members
            member_data = []

            for member in members:
                member_info = {
                    "이름": member.name,
                    "ID": str(member.id),
                    "아바타_URL": str(member.avatar.url) if member.avatar else str(member.default_avatar.url),
                    "식별자": member.discriminator,
                    "상태": str(member.status),
                    "가입일": str(member.joined_at)
                }
                member_data.append(member_info)

            try:
                with open("members_list.json", "w", encoding="utf-8") as f:
                    json.dump(member_data, f, indent=4, ensure_ascii=False) # 한글 인코딩을 위해 ensure_ascii=False 추가

                await message.channel.send("> 멤버 목록:", file=discord.File("members_list.json"), delete_after=60)

            except Exception as e:
                await message.channel.send(f'> **[오류]**: 멤버를 가져오거나 파일에 저장하지 못했습니다: `{str(e)}`', delete_after=5)
            finally:
                if os.path.exists("members_list.json"):
                    os.remove("members_list.json")

        elif command == "멘트저장":
            await message.delete()
            parts = args.split(' ', 1)
            if len(parts) < 2:
                await message.channel.send(f"> **[오류]**: 키워드와 내용을 입력하세요. 예: `{prefix}멘트저장 안녕 안녕하세요`", delete_after=5)
                return
            keyword, content = parts[0], parts[1]
            config.setdefault("saved_mentions", {})[keyword] = content
            save_config(config)
            await message.channel.send(f"> 멘트 저장 완료: 키워드 `{keyword}`", delete_after=5)

        elif command == "멘트":
            await message.delete()
            keyword = args.strip()
            if not keyword:
                await message.channel.send(f"> **[오류]**: 키워드를 입력하세요. 예: `{prefix}멘트 안녕`", delete_after=5)
                return
            content = config.get("saved_mentions", {}).get(keyword)
            if not content:
                await message.channel.send(f"> **[오류]**: 키워드 `{keyword}`에 저장된 멘트가 없습니다.", delete_after=5)
                return
            await message.channel.send(content)

        elif command == "멘트목록":
            await message.delete()
            if not config.get("saved_mentions", {}):
                await message.channel.send(f"> 저장된 멘트가 없습니다.", delete_after=5)
                return
            
            ment_list = "\n".join(config["saved_mentions"].keys())
            if len(ment_list) > 1900:
                await message.channel.send(f"> **멘트 목록** (일부만 표시)\n> {ment_list[:1900]}...", delete_after=15)
            else:
                await message.channel.send(f"> **멘트 목록**\n> {ment_list}", delete_after=15)

        elif command == "멘트삭제":
            await message.delete()
            keyword = args.strip()
            if not keyword:
                await message.channel.send(f"> **[오류]**: 키워드를 입력하세요. 예: `{prefix}멘트삭제 안녕`", delete_after=5)
                return
            if keyword in config.get("saved_mentions", {}):
                del config["saved_mentions"][keyword]
                save_config(config)
                await message.channel.send(f"> 멘트 `{keyword}` 삭제 완료", delete_after=5)
            else:
                await message.channel.send(f"> **[오류]**: 키워드 `{keyword}`에 저장된 멘트가 없습니다.", delete_after=5)

        elif command == "서버테러":
            await message.delete()
            try:
                guild_id = int(args)
            except ValueError:
                guild_id = None
            if not guild_id:
                await message.channel.send(f"> **[오류]**: 서버 ID를 입력하세요. 예: `{prefix}서버테러 123456789`", delete_after=5)
                return
            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send(f"> **[오류]**: 서버를 찾을 수 없습니다.", delete_after=5)
                return
            if not message.guild.me.guild_permissions.administrator:
                await message.channel.send(f"> **[오류]**: 관리자 권한이 없습니다.", delete_after=5)
                return
            await message.channel.send(f"> **[경고]**: 서버 테러는 구현되지 않았습니다. 서버 ID: `{guild_id}` (이 기능은 Discord 이용 약관에 위배될 수 있습니다.)", delete_after=10)

        elif command == "서버복제":
            await message.delete()
            parts = args.split(' ')
            source_guild_id = int(parts[0]) if parts and parts[0].isdigit() else None
            target_guild_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            if not source_guild_id or not target_guild_id:
                await message.channel.send(f"> **[오류]**: 원본 서버 ID와 대상 서버 ID를 입력하세요. 예: `{prefix}서버복제 123456789 987654321`", delete_after=5)
                return
            await message.channel.send(f"> **[오류]**: 서버 복제 기능은 구현되지 않았습니다. (이 기능은 Discord 이용 약관에 위배될 수 있습니다.)", delete_after=10)

        elif command == "guildrename" or command == "grename":
            await message.delete()
            name = args.strip()
            if not name:
                await message.channel.send("> **[오류]**: 잘못된 명령어.\n> __명령어__: `guildrename <이름>`", delete_after=5)
                return

            if not message.guild:
                await message.channel.send("> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.", delete_after=5)
                return

            if not message.guild.me.guild_permissions.manage_guild:
                await message.channel.send(f'> **[오류]**: 권한이 없습니다.', delete_after=5)
                return

            try:
                old_name = message.guild.name
                await message.guild.edit(name=name)
                await message.channel.send(f"> 서버 이름이 '{old_name}'에서 '{name}'으로 변경되었습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f'> **[오류]**: 서버 이름을 변경할 수 없습니다.\n> __오류__: `{str(e)}`', delete_after=5)

        elif command == "purge":
            await message.delete()
            try:
                num_messages = int(args) if args else 1
            except ValueError:
                num_messages = 1

            if not message.guild:
                await message.channel.send("> **[오류]**: 이 명령어는 서버에서만 사용할 수 있습니다.", delete_after=5)
                return

            if not message.author.guild_permissions.manage_messages:
                await message.channel.send("> **[오류]**: 메시지를 삭제할 권한이 없습니다.", delete_after=5)
                return

            if 1 <= num_messages <= 100:
                try:
                    deleted_messages = await message.channel.purge(limit=num_messages + 1)
                    await message.channel.send(f"> **{len(deleted_messages) - 1}**개의 메시지가 삭제되었습니다.", delete_after=5)
                except Exception as e:
                    await message.channel.send(f'> **[오류]**: 메시지를 삭제하지 못했습니다: `{str(e)}`', delete_after=5)
            else:
                await message.channel.send("> **[오류]**: 숫자는 1에서 100 사이여야 합니다.", delete_after=5)

        elif command == "보이스입장":
            await message.delete()
            try:
                voice_channel_id = int(args)
            except ValueError:
                voice_channel_id = None
            if not voice_channel_id:
                await message.channel.send(f"> **[오류]**: 음성 채널 ID를 입력하세요. 예: `{prefix}보이스입장 123456789`", delete_after=5)
                return
            channel = client.get_channel(voice_channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                await message.channel.send(f"> **[오류]**: 유효한 음성 채널 ID를 입력하세요.", delete_after=5)
                return
            try:
                if message.guild.voice_client:
                    await message.guild.voice_client.move_to(channel)
                else:
                    await channel.connect()
                await message.channel.send(f"> 음성 채널 `{channel.name}`에 입장했습니다.", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 음성 채널에 연결할 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 음성 채널 입장 실패: `{str(e)}`", delete_after=5)

        elif command == "보이스퇴장":
            await message.delete()
            if not message.guild.voice_client:
                await message.channel.send(f"> **[오류]**: 음성 채널에 연결되어 있지 않습니다.", delete_after=5)
                return
            try:
                await message.guild.voice_client.disconnect()
                await message.channel.send(f"> 음성 채널에서 퇴장했습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 음성 채널 퇴장 실패: `{str(e)}`", delete_after=5)

        elif command == "청소":
            await message.delete()
            if not message.guild:
                await message.channel.send(f"> **[오류]**: 서버에서만 사용 가능합니다.", delete_after=5)
                return
            try:
                amount = int(args) if args else 1
            except ValueError:
                amount = 1
            if amount <= 0 or amount > 25:
                await message.channel.send(f"> **[오류]**: 삭제 개수는 1~25 사이여야 합니다.", delete_after=5)
                return
            if not message.author.guild_permissions.manage_messages:
                await message.channel.send(f"> **[오류]**: 메시지 관리 권한이 없습니다.", delete_after=5)
                return
            try:
                deleted = await message.channel.purge(limit=amount + 1)
                await message.channel.send(f"> **{len(deleted)-1}개** 메시지 삭제 완료", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 메시지 삭제 실패: `{str(e)}`", delete_after=5)

        elif command == "서버추방":
            await message.delete()
            user_to_kick = message.mentions[0] if message.mentions else None
            reason = args.split(' ', 1)[1] if len(args.split(' ', 1)) > 1 else None
            if not user_to_kick:
                await message.channel.send(f"> **[오류]**: 유저를 멘션하세요. 예: `{prefix}서버추방 @유저`", delete_after=5)
                return
            if not message.author.guild_permissions.kick_members:
                await message.channel.send(f"> **[오류]**: 추방 권한이 없습니다.", delete_after=5)
                return
            if user_to_kick == message.author:
                await message.channel.send(f"> **[오류]**: 자신을 추방할 수 없습니다.", delete_after=5)
                return
            if user_to_kick.top_role >= message.author.top_role and user_to_kick != message.guild.owner:
                await message.channel.send(f"> **[오류]**: 해당 유저를 추방할 권한이 없습니다 (역할 순위).", delete_after=5)
                return
            try:
                await message.guild.kick(user_to_kick, reason=reason)
                await message.channel.send(f"> `{user_to_kick.name}`을(를) 추방했습니다. (사유: `{reason or '없음'}`)", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 추방 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 추방 실패: `{str(e)}`", delete_after=5)

        elif command == "서버차단":
            await message.delete()
            user_to_ban = message.mentions[0] if message.mentions else None
            reason = args.split(' ', 1)[1] if len(args.split(' ', 1)) > 1 else None
            if not user_to_ban:
                await message.channel.send(f"> **[오류]**: 유저를 멘션하세요. 예: `{prefix}서버차단 @유저`", delete_after=5)
                return
            if not message.author.guild_permissions.ban_members:
                await message.channel.send(f"> **[오류]**: 차단 권한이 없습니다.", delete_after=5)
                return
            if user_to_ban == message.author:
                await message.channel.send(f"> **[오류]**: 자신을 차단할 수 없습니다.", delete_after=5)
                return
            if user_to_ban.top_role >= message.author.top_role and user_to_ban != message.guild.owner:
                await message.channel.send(f"> **[오류]**: 해당 유저를 차단할 권한이 없습니다 (역할 순위).", delete_after=5)
                return
            try:
                await message.guild.ban(user_to_ban, reason=reason)
                await message.channel.send(f"> `{user_to_ban.name}`을(를) 차단했습니다. (사유: `{reason or '없음'}`)", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 차단 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 차단 실패: `{str(e)}`", delete_after=5)

        elif command == "서버차단해제":
            await message.delete()
            parts = args.split(' ', 1)
            user_id = int(parts[0]) if parts and parts[0].isdigit() else None
            reason = parts[1] if len(parts) > 1 else None
            if not user_id:
                await message.channel.send(f"> **[오류]**: 유저 ID를 입력하세요. 예: `{prefix}서버차단해제 123456789`", delete_after=5)
                return
            if not message.author.guild_permissions.ban_members:
                await message.channel.send(f"> **[오류]**: 차단 해제 권한이 없습니다.", delete_after=5)
                return
            try:
                user_to_unban = await client.fetch_user(user_id)
                await message.guild.unban(user_to_unban, reason=reason)
                await message.channel.send(f"> `{user_to_unban.name}`의 차단을 해제했습니다. (사유: `{reason or '없음'}`)", delete_after=5)
            except discord.NotFound:
                await message.channel.send(f"> **[오류]**: 해당 ID를 가진 차단된 유저를 찾을 수 없습니다.", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 차단 해제 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 차단 해제 실패: `{str(e)}`", delete_after=5)

        elif command == "타임아웃":
            await message.delete()
            user_to_timeout = message.mentions[0] if message.mentions else None
            parts = args.split(' ', 2)
            seconds = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            reason = parts[2] if len(parts) > 2 else None
            if not user_to_timeout or not seconds:
                await message.channel.send(f"> **[오류]**: 유저와 시간을 입력하세요. 예: `{prefix}타임아웃 @유저 60 사유`", delete_after=5)
                return
            if not message.author.guild_permissions.moderate_members:
                await message.channel.send(f"> **[오류]**: 타임아웃 권한이 없습니다.", delete_after=5)
                return
            if seconds <= 0:
                await message.channel.send(f"> **[오류]**: 시간은 0보다 커야 합니다.", delete_after=5)
                return
            try:
                duration = datetime.timedelta(seconds=seconds)
                if duration > datetime.timedelta(days=28):
                    await message.channel.send(f"> **[오류]**: 타임아웃 기간은 최대 28일입니다.", delete_after=5)
                    return

                await user_to_timeout.timeout(duration, reason=reason)
                await message.channel.send(f"> `{user_to_timeout.name}`에게 `{seconds}`초 타임아웃 적용 (사유: `{reason or '없음'}`)", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 타임아웃 권한이 없습니다. (봇 역할이 해당 유저의 역할보다 낮거나 권한이 없음)", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 타임아웃 적용 실패: `{str(e)}`", delete_after=5)

        elif command == "타임아웃해제":
            await message.delete()
            user_to_untimeout = message.mentions[0] if message.mentions else None
            if not user_to_untimeout:
                await message.channel.send(f"> **[오류]**: 유저를 멘션하세요. 예: `{prefix}타임아웃해제 @유저`", delete_after=5)
                return
            if not message.author.guild_permissions.moderate_members:
                await message.channel.send(f"> **[오류]**: 타임아웃 해제 권한이 없습니다.", delete_after=5)
                return
            try:
                await user_to_untimeout.timeout(None)
                await message.channel.send(f"> `{user_to_untimeout.name}`의 타임아웃을 해제했습니다.", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 타임아웃 해제 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 타임아웃 해제 실패: `{str(e)}`", delete_after=5)

        elif command == "역할생성":
            await message.delete()
            role_name = args.strip()
            if not role_name:
                await message.channel.send(f"> **[오류]**: 역할 이름을 입력하세요. 예: `{prefix}역할생성 관리자`", delete_after=5)
                return
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(f"> **[오류]**: 역할 관리 권한이 없습니다.", delete_after=5)
                return
            try:
                role = await message.guild.create_role(name=role_name)
                await message.channel.send(f"> 역할 `{role_name}` 생성 완료", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 역할 생성 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 역할 생성 실패: `{str(e)}`", delete_after=5)

        elif command == "역할지급":
            await message.delete()
            role_to_give = message.role_mentions[0] if message.role_mentions else None
            user_to_give = message.mentions[0] if message.mentions else None
            if not role_to_give or not user_to_give:
                await message.channel.send(f"> **[오류]**: 역할과 유저를 입력하세요. 예: `{prefix}역할지급 @역할 @유저`", delete_after=5)
                return
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(f"> **[오류]**: 역할 관리 권한   없습니다.", delete_after=5)
                return
            if role_to_give >= message.author.top_role:
                await message.channel.send(f"> **[오류]**: 자신보다 높거나 같은 역할을 부여할 수 없습니다.", delete_after=5)
                return
            if user_to_give.top_role >= message.author.top_role and user_to_give != message.guild.owner:
                await message.channel.send(f"> **[오류]**: 해당 유저의 역할 순위가 자신보다 높아 역할을 지급할 수 없습니다.", delete_after=5)
                return
            try:
                await user_to_give.add_roles(role_to_give)
                await message.channel.send(f"> `{user_to_give.name}`에게 `{role_to_give.name}` 역할 지급 완료", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 역할 지급 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 역할 지급 실패: `{str(e)}`", delete_after=5)

        elif command == "역할제거":
            await message.delete()
            role_to_remove = message.role_mentions[0] if message.role_mentions else None
            user_to_remove = message.mentions[0] if message.mentions else None
            if not role_to_remove or not user_to_remove:
                await message.channel.send(f"> **[오류]**: 역할과 유저를 입력하세요. 예: `{prefix}역할제거 @역할 @유저`", delete_after=5)
                return
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(f"> **[오류]**: 역할 관리 권한이 없습니다.", delete_after=5)
                return
            if role_to_remove >= message.author.top_role:
                await message.channel.send(f"> **[오류]**: 자신보다 높거나 같은 역할을 제거할 수 없습니다.", delete_after=5)
                return
            if user_to_remove.top_role >= message.author.top_role and user_to_remove != message.guild.owner:
                await message.channel.send(f"> **[오류]**: 해당 유저의 역할 순위가 자신보다 높아 역할을 제거할 수 없습니다.", delete_after=5)
                return
            try:
                await user_to_remove.remove_roles(role_to_remove)
                await message.channel.send(f"> `{user_to_remove.name}`의 `{role_to_remove.name}` 역할 제거 완료", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 역할 제거 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 역할 제거 실패: `{str(e)}`", delete_after=5)

        elif command == "역할삭제":
            await message.delete()
            role_to_delete = message.role_mentions[0] if message.role_mentions else None
            if not role_to_delete:
                await message.channel.send(f"> **[오류]**: 역할을 입력하세요. 예: `{prefix}역할삭제 @역할`", delete_after=5)
                return
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(f"> **[오류]**: 역할 관리 권한이 없습니다.", delete_after=5)
                return
            if role_to_delete >= message.author.top_role:
                await message.channel.send(f"> **[오류]**: 자신보다 높거나 같은 역할을 삭제할 수 없습니다.", delete_after=5)
                return
            try:
                await role_to_delete.delete()
                await message.channel.send(f"> 역할 `{role_to_delete.name}` 삭제 완료", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 역할 삭제 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 역할 삭제 실패: `{str(e)}`", delete_after=5)

        elif command == "별명변경":
            await message.delete()
            user_to_nick = message.mentions[0] if message.mentions else None
            nickname = args.split(' ', 1)[1] if len(args.split(' ', 1)) > 1 else None
            if not user_to_nick or nickname is None:
                await message.channel.send(f"> **[오류]**: 유저와 별명을 입력하세요. 예: `{prefix}별명변경 @유저 새별명`", delete_after=5)
                return
            if not message.author.guild_permissions.manage_nicknames:
                await message.channel.send(f"> **[오류]**: 별명 관리 권한이 없습니다.", delete_after=5)
                return
            if user_to_nick == message.author and not message.author.guild_permissions.change_nickname:
                await message.channel.send(f"> **[오류]**: 자신의 별명을 변경할 권한이 없습니다.", delete_after=5)
                return
            if user_to_nick != message.author and user_to_nick.top_role >= message.author.top_role and user_to_nick != message.guild.owner:
                await message.channel.send(f"> **[오류]**: 해당 유저의 역할 순위가 자신보다 높아 별명을 변경할 수 없습니다.", delete_after=5)
                return
            try:
                await user_to_nick.edit(nick=nickname if nickname else None)
                await message.channel.send(f"> `{user_to_nick.name}`의 별명을 `{nickname if nickname else '없음'}`로 변경했습니다.", delete_after=5)
            except discord.Forbidden:
                await message.channel.send(f"> **[오류]**: 봇에게 별명 변경 권한이 없습니다.", delete_after=5)
            except Exception as e:
                await message.channel.send(f"> **[오류]**: 별명 변경 실패: `{str(e)}`", delete_after=5)

        elif command == "nitro":
            await message.delete()
            await message.channel.send(f"https://discord.gift/{''.join(random.choices(string.ascii_letters + string.digits, k=16))}", delete_after=15)

        elif command == "whremove":
            await message.delete()
            webhook = args.strip()
            if not webhook:
                await message.channel.send(f'> **[오류]**: 잘못된 입력\n> __명령어__: `{prefix}whremove <웹훅>`', delete_after=5)
                return
            try:
                requests.delete(webhook.rstrip(), timeout=5)
                await message.channel.send(f'> 웹훅이 삭제되었습니다!', delete_after=5)
            except requests.exceptions.RequestException as e:
                await message.channel.send(f'> **[오류]**: 웹훅을 삭제할 수 없습니다.\n> __오류__: `{str(e)}`', delete_after=5)
            except Exception as e:
                await message.channel.send(f'> **[오류]**: 예상치 못한 오류가 발생했습니다: `{str(e)}`', delete_after=5)


bot = commands.Bot(command_prefix=".", self_bot=True)

@bot.event
async def on_ready():
    print(f"{y}로그인 성공: {bot.user}{w}")

if __name__ == "__main__":
    try:
        print(f"{y}봇을 시작합니다...{w}")
        client.run(token)
    except discord.LoginFailure:
        print(f"{y}토큰이 유효하지 않습니다. 올바른 토큰을 입력하세요.{w}")
        time.sleep(5)
        exit(1)
    except Exception as e:
        print(f"{y}봇 시작 중 오류 발생: {str(e)}{w}")
        time.sleep(5)
        exit(1)
    finally:
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
        print(f"{y}블랙너스 셀프봇이 종료되었습니다. 개발자: 김민준{w}")
