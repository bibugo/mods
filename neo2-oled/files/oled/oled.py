#!/usr/bin/env python
# -*- encoding:utf8 -*-

import os
import sys
import commands
import time
import signal
import socket
import subprocess
import smbus
import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import RPi.GPIO as GPIO

global pageSleep
pageSleep=60
global pageSleepCountdown
pageSleepCountdown=pageSleep

rebootDelay = 6

gap = 4
oled_width		= 128
oled_height		=  64

# SSD1306 --> 0
# SH1106  --> 2
oled_offset_x	= 0

font_title		= ImageFont.truetype('/usr/share/oled/fz12.TTF', 12, encoding='unic')
font_info		= ImageFont.truetype('/usr/share/oled/fz12.TTF', 14, encoding='unic')
font_audio		= ImageFont.load_default()
font_time		= ImageFont.truetype('/usr/share/oled/fz12.TTF', 28);
font_date		= ImageFont.truetype('/usr/share/oled/fz12.TTF', 16);

font_title_offset_y = 2

bus = smbus.SMBus(0)
OLED_address     = 0x3c
OLED_CommandMode = 0x00
OLED_DataMode    = 0x40

def oled_init():
	cmd	= []
	cmd	+= [0xAE]	#display off
	cmd	+= [0x40]	#set display start line
	cmd	+= [0x81]	# Contrast
	cmd	+= [0x80]	# 0 - 255, default=0x80
	cmd	+= [0xA1]	#set segment remap
	cmd	+= [0xA6]	#normal / reverse
	cmd	+= [0xA8]	#multiplex ratio
	cmd	+= [0x3F]	#duty = 1/64
	cmd	+= [0xC8]	#Com scan direction
	cmd	+= [0xD3]	#set display offset
	cmd	+= [0x00]	
	cmd	+= [0xD5]	#set osc division
	cmd	+= [0x80]
	cmd	+= [0xD9]	#set pre-charge period
	cmd	+= [0xF1]
	cmd	+= [0xDA]	#set COM pins
	cmd	+= [0x12]
	cmd	+= [0xDB]	#set vcomh
	cmd	+= [0x40]
	cmd	+= [0x8D]	#set charge pump enable
	cmd	+= [0x14]
	cmd	+= [0x20]	#set addressing mode
	cmd	+= [0x02]	#set page addressing mode
	cmd	+= [0xAF]	#display ON

	for byte in cmd:
		try:
			bus.write_byte_data(OLED_address,OLED_CommandMode,byte)
		except IOError:
			print("IOError")
			return -1


def oled_drawImage(image):
	if image.mode != '1' and image.mode != 'L':
		raise ValueError('Image must be in mode 1.')

	imwidth, imheight = image.size
	if imwidth != oled_width or imheight != oled_height:
		raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
		.format(oled_width, oled_height))

	# Grab all the pixels from the image, faster than getpixel.
	pix		= image.load()

	pages	= oled_height / 8;
	block	= oled_width / 32;

	for page in range(pages):
		addr	= [];
		addr	+= [0xB0 | page];	# Set Page Address
		addr	+= [0x10];	# Set Higher Column Address
		addr	+= [0x00 | oled_offset_x];	# Set Lower Column Address

		try:
			bus.write_i2c_block_data(OLED_address,OLED_CommandMode,addr)
		except IOError:
			print("IOError")
			return -1

		for blk in range(block):
			data=[]
			for b in range(32):
				x	= blk * 32 + b;
				y	= page * 8

				data.append(
					((pix[(x, y+0)] >> 7) << 0) | \
					((pix[(x, y+1)] >> 7) << 1) | \
					((pix[(x, y+2)] >> 7) << 2) | \
					((pix[(x, y+3)] >> 7) << 3) | \
					((pix[(x, y+4)] >> 7) << 4) | \
					((pix[(x, y+5)] >> 7) << 5) | \
					((pix[(x, y+6)] >> 7) << 6) | \
					((pix[(x, y+7)] >> 7) << 7) );

			try:
				bus.write_i2c_block_data(OLED_address,OLED_DataMode,data)
			except IOError:
				print("IOError")
				return -1

# initialize OLED
oled_init()

# OLED images
image			= Image.new('L', (oled_width, oled_height))
draw			= ImageDraw.Draw(image)
draw.rectangle((0,0,oled_width,oled_height), outline=0, fill=0)

print("----- start ----------")

def getIP():
	cmd = "ubus call network.interface.lan status | grep \"address\" | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'"
	ip = subprocess.check_output(cmd,shell = True)
	return str(ip)

def getCPUuse():
	cmd = "echo -e `expr 100 - $(top -n 1 | grep 'CPU:' | awk -F '%' '{ print $4 }' | awk -F ' ' '{ print $2 }')`%"
	CPU = subprocess.check_output(cmd,shell = True)
	return str(CPU)

def getNetstat():
	cmd = "ifstat -i eth0 -q 1 1 | awk 'NR>2 {print $1}'"
	net = subprocess.check_output(cmd,shell = True).replace("\n", "")
	if float(net) > 1024:
		net = float(net) / 1024
		out = '网速: '+str(int(float(net)))+'MB/S'
	else:
		out = '网速: '+str(int(float(net)))+'KB/S'
	return out

def getServerType():
	cmd = "uci get shadowsocksr.@global[0].global_server"
	glo = subprocess.check_output(cmd,shell = True)
	
	typeCmd = "uci get shadowsocksr."+glo+".type"
	globalServer = subprocess.check_output(typeCmd.replace("\n", ""),shell = True)
	return globalServer.rstrip()

def getServerName():
	cmd = "uci get shadowsocksr.@global[0].global_server"
	glo = subprocess.check_output(cmd,shell = True)
	
	typeCmd = "uci get shadowsocksr."+glo+".alias"
	globalServer = subprocess.check_output(typeCmd.replace("\n", ""),shell = True)
	return globalServer.rstrip()

def restoreNetwork():
    subprocess.call(("uci delete network.lan"),shell = True)
    subprocess.call(("uci set network.lan=interface"),shell = True)
    subprocess.call(("uci set network.lan.ifname=eth0"),shell = True)
    subprocess.call(("uci set network.lan.proto=dhcp"),shell = True)
    subprocess.call(("uci commit network"),shell = True)
    subprocess.call(("/etc/init.d/network restart"),shell = True)

def resetPassword():
	subprocess.call(("sed -i -e 's/^root:[^:]\+:/root::/' etc/shadow"),shell = True)

#switch
state = 1
menu_select = 0

SWITCH_PIN1 = 11
SWITCH_PIN2 = 13
SWITCH_PIN3 = 15
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(SWITCH_PIN1,GPIO.IN,GPIO.PUD_DOWN)
GPIO.setup(SWITCH_PIN2,GPIO.IN,GPIO.PUD_DOWN)
GPIO.setup(SWITCH_PIN3,GPIO.IN,GPIO.PUD_DOWN)

GPIO.add_event_detect(SWITCH_PIN1, GPIO.RISING,bouncetime=200)  # add rising edge detection on a channel
GPIO.add_event_detect(SWITCH_PIN2, GPIO.RISING,bouncetime=200)  # add rising edge detection on a channel
GPIO.add_event_detect(SWITCH_PIN3, GPIO.RISING,bouncetime=200)  # add rising edge detection on a channel


nodefound = True
nodenum = 0
while nodefound:
	try:
		print subprocess.check_output("uci get shadowsocksr.@servers["+str(nodenum)+"].alias".replace("\n", ""),shell = True).rstrip()
		nodenum = nodenum + 1
	except:
		nodefound = False

while True:	
	if (state == 1) and (pageSleepCountdown > 0):
		# Draw Cpu usage
		cpu_image     = Image.new('L', (oled_width, 16))
		cpu_draw      = ImageDraw.Draw(cpu_image)
		cpu_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
		cpu_draw.text((0,font_title_offset_y), unicode('CPU使用率:'+getCPUuse(),'utf-8'), font=font_title, fill=255)
		image.paste(cpu_image, (gap,0))
		
		# Draw IP address
		try:
			ip_image     = Image.new('L', (oled_width, 16))
			ip_draw      = ImageDraw.Draw(ip_image)
			ip_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			ip_draw.text((0,font_title_offset_y), unicode('IP:'+getIP(),'utf-8'), font=font_title, fill=255)
			image.paste(ip_image, (gap,16))
		except:
			ip_image     = Image.new('L', (oled_width, 16))
			ip_draw      = ImageDraw.Draw(ip_image)
			ip_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			ip_draw.text((0,font_title_offset_y), unicode('IP地址获取中...','utf-8'), font=font_title, fill=255)
			image.paste(ip_image, (gap,16))
		
		# Draw Net stat
		try:
			net_image     = Image.new('L', (oled_width, 16))
			net_draw      = ImageDraw.Draw(net_image)
			net_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			net_draw.text((0,font_title_offset_y), unicode(getNetstat(),'utf-8'), font=font_title, fill=255)
			image.paste(net_image, (gap,48))
		except:
			net_image     = Image.new('L', (oled_width, 16))
			net_draw      = ImageDraw.Draw(net_image)
			net_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			net_draw.text((0,font_title_offset_y), unicode("当前无网络",'utf-8'), font=font_title, fill=255)
			image.paste(net_image, (gap,48))

		# Draw Node info
		try:
			node_image     = Image.new('L', (oled_width, 16))
			node_draw      = ImageDraw.Draw(node_image)
			node_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			node_draw.text((0,font_title_offset_y), unicode('节点:('+getServerType()+')'+getServerName(),'utf-8'), font=font_title, fill=255)
			image.paste(node_image, (gap,32))
		except:
			node_image     = Image.new('L', (oled_width, 16))
			node_draw      = ImageDraw.Draw(node_image)
			node_draw.rectangle((0,0, oled_width, 16), outline=0, fill=0)
			node_draw.text((0,font_title_offset_y), unicode("透明代理当前未运行",'utf-8'), font=font_title, fill=255)
			image.paste(node_image, (gap,32))

	elif (state == 2) and (pageSleepCountdown > 0):
		menu_image     = Image.new('L', (oled_width, oled_height))
		menu_draw      = ImageDraw.Draw(menu_image)
		menu_draw.rectangle((0,16 + menu_select*16, oled_width, 32 + menu_select*16), outline=0, fill=255)
		menu_draw.text((0,font_title_offset_y), unicode('[ 菜单 ]','utf-8'), font=font_title, fill=255)
		if menu_select == 0:
		    menu_draw.text((0,16+font_title_offset_y), unicode('清除密码','utf-8'), font=font_title, fill=0)
		else:
		    menu_draw.text((0,16+font_title_offset_y), unicode('清除密码','utf-8'), font=font_title, fill=255)
		if menu_select == 1:
		    menu_draw.text((0,32+font_title_offset_y), unicode('恢复网络设置','utf-8'), font=font_title, fill=0)
		else:
		    menu_draw.text((0,32+font_title_offset_y), unicode('恢复网络设置','utf-8'), font=font_title, fill=255)
		if menu_select == 2:
		    menu_draw.text((0,48+font_title_offset_y), unicode('重新启动','utf-8'), font=font_title, fill=0)
		else:
		    menu_draw.text((0,48+font_title_offset_y), unicode('重新启动','utf-8'), font=font_title, fill=255)

		image.paste(menu_image, (gap,0))

	elif (state == 3) and (pageSleepCountdown > 0):
		info_image     = Image.new('L', (oled_width, oled_height))
		info_draw      = ImageDraw.Draw(info_image)
		info_draw.rectangle((0,0,oled_width,oled_height), outline=0, fill=0)
		if rebootDelay == 0 :
		    msg=unicode('系统重启中...','utf-8')
		    info_draw.text((28,18), msg, font=font_title, fill=255)
		    image.paste(info_image, (0,0))
		    oled_drawImage(image)
		    time.sleep(1)
		    os.system('reboot')
		else:
		    msg=unicode('系统将在'+str(rebootDelay - 1)+'秒后重启','utf-8')
		    info_draw.text((12,18), msg, font=font_title, fill=255)
		    image.paste(info_image, (0,0))

		rebootDelay = rebootDelay - 1
		time.sleep(1)

	else:
		# clear screen
		draw.rectangle((0,0,oled_width,oled_height), outline=0, fill=0)

	oled_drawImage(image)
#	time.sleep(1)

	if GPIO.event_detected(SWITCH_PIN1):
		print 'Button1 pressed'
		state = 1
		pageSleepCountdown = pageSleep

	if GPIO.event_detected(SWITCH_PIN2):
		print 'Button2 pressed'
		if state == 2:
		    if menu_select >= 2:
		        menu_select = 0
		    else:
		        menu_select = menu_select + 1
		else:
		    state = 2
		pageSleepCountdown = pageSleep

	if GPIO.event_detected(SWITCH_PIN3):
		if state == 2:
		    print 'Button3 pressed' + str(menu_select)
		    if menu_select == 2:
		        state = 3
		    elif menu_select == 1:
		        restoreNetwork()
		        state = 1
		    elif menu_select == 0:
		        resetPassword()
		        state = 1
		else:
		    state = 2
		pageSleepCountdown = pageSleep

	if pageSleepCountdown == 0:
		pageSleepCountdown = 0
	else:
		pageSleepCountdown = pageSleepCountdown - 1
