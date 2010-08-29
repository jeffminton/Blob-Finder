#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#	   untitled.py
#	   
#	   Copyright 2010 Jeffrey Minton <ffej@blinking-book>
#	   
#	   This program is free software; you can redistribute it and/or modify
#	   it under the terms of the GNU General Public License as published by
#	   the Free Software Foundation; either version 2 of the License, or
#	   (at your option) any later version.
#	   
#	   This program is distributed in the hope that it will be useful,
#	   but WITHOUT ANY WARRANTY; without even the implied warranty of
#	   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	   GNU General Public License for more details.
#	   
#	   You should have received a copy of the GNU General Public License
#	   along with this program; if not, write to the Free Software
#	   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#	   MA 02110-1301, USA.

import cv
import time
from unionfind import *

def main():
	#img = cv.LoadImage("0.bmp")
	cv.NamedWindow("orig")
	cv.NamedWindow("img")
	cv.NamedWindow("blobimg")
	cap = cv.CaptureFromCAM(0)
	print "setting props"
	cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH, 320)
	cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
	#~ cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_EXPOSURE, -.2)
	#~ expo = cv.GetCaptureProperty(cap, cv.CV_CAP_PROP_EXPOSURE)
	#~ print expo
	finished = False
	while(finished == False):
		orig = cv.QueryFrame(cap)
		cv.ShowImage("orig", orig)
		k = cv.WaitKey(5)
		print k
		if k % 0x100 == 27:
			finished = True
	#~ print "getting frame"
	#~ orig = cv.QueryFrame(cap)
	#~ print "getting next frame"
	#~ orig = cv.QueryFrame(cap)
	img = cv.CreateImage((320, 240), cv.IPL_DEPTH_8U, 3)
	cv.Smooth(orig, img, cv.CV_GAUSSIAN, 3) 
	
	blobImg, region2color, region2pix = findBlob(img, 10)
	
	#~ cc = cv.FloodFill(img, (0, 0), (255, 0, 0), (14, 14, 14), (14, 14, 14))
	#~ print cc
	
	color = (75, 0, 0) 
	region = findColor(color, blobImg, region2color, region2pix)
	print "best color: ", region2color[region]
	
	regionMid = midMass(region2pix, region)
	print "Middle of Region: ", regionMid
	
	black = False
	for pix in region2pix[region]:
		if(black == True):
			blobImg[pix[0], pix[1]] = (0, 0, 0)
			black = False
		else:
			blobImg[pix[0], pix[1]] = (255, 255, 255)
			black = True
	
	blobImg[regionMid[0], regionMid[1]] = (0, 0, 255)
	
	cv.ShowImage("orig", orig)
	cv.ShowImage("img", img)
	cv.ShowImage("blobimg", blobImg)
	
	finished = False
	while(finished == False):
		k = cv.WaitKey(5)
		if k % 0x100 == 27:
			finished = True
	
	cv.SaveImage("blobImg.bmp", blobImg)
	cv.DestroyWindow("orig")
	cv.DestroyWindow("img")
	cv.DestroyWindow("blobimg")


def midMass(region2pix, region):
	maxX = region2pix[region][0][1]
	minX = region2pix[region][0][1]
	maxY = region2pix[region][0][0]
	minY = region2pix[region][0][0]
	
	for coord in region2pix[region]:
		if(coord[1] > maxX):
			maxX = coord[1]
		if(coord[1] < minX):
			minX = coord[1]
		if(coord[0] > maxY):
			maxY = coord[0]
		if(coord[0] < minY):
			minY = coord[0]
			
	midX = (minX + maxX) / 2
	midY = (minY + maxY) / 2
	
	return (midY, midX)

def findColor(color, blobImg, region2color, region2pix):
	bestKey = None
	bestColor = None
	color = {"blue" : color[2], "green" : color[1], "red" : color[0]}
	prim = None
	sec = []
	
	#get the primary and secondary colors
	for key in color.keys():
		if(prim == None):
			prim = key
		elif(color[key] > color[prim]):
			prim = key
	for key in color.keys():
		if(key != prim):
			sec.append(key)
			
	for key in region2color.keys():
		regColor = region2color[key]
		regColor = {"blue" : regColor[0], "green" : regColor[1], "red" : regColor[2]}
		offset = regColor[prim] - color[prim]
		newRegColor = {"blue" : regColor["blue"] - offset, "green" : regColor["green"] - offset, "red" : regColor["red"] - offset}
		
		if(newRegColor[prim] >= color[prim] and newRegColor[sec[0]] <= color[sec[0]] and newRegColor[sec[1]] <= color[sec[1]]):
			if(bestKey == None):
				bestKey = key
			elif(len(region2pix[key]) > len(region2pix[bestKey])):
				bestKey = key
				
	return bestKey

def findBlob(img, threshold):
	#pixMap = [(0, -1), (-1, 0), (0, 1), (1, 0)]
	#pixMap = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]
	#pixMap = [(0, -1), (-1, 0)]
	uf = UnionFind()
	west = (0, -1)
	north = (-1, 0)
	region2pix = {}
	region2color = {}
	pix2region = {}
	similar = {}
	sameRegion = []
	regionCnt = 0
	timeComp = 0
	timeReg = 0
	timeJoinReg = 0
	found = False
	matchWest = False
	matchNorth = False
	
	'''	Pass One	'''
	print "Pass One"
	for y in range(img.height):
		for x in range(img.width):
			matchWest = False
			matchNorth = False
			pixCheck = [y, x]
			#get the address of the pixel to compare to
			pixWest = getPixOffset(pixCheck, west, img)
			pixNorth = getPixOffset(pixCheck, north, img)
			
			#check if the average color distance is less than threshold
			if(checkPixels(pixCheck, pixWest, img, threshold) == True):
				if(pix2region.has_key(str(pixWest))):	
					#set pixCheck to the same region as pixWest
					matchWest = True
					pix2region[str(pixCheck)] = pix2region[str(pixWest)]
			
			if(checkPixels(pixCheck, pixNorth, img, threshold) == True):
				if(pix2region.has_key(str(pixNorth))):
					matchNorth = True
					if(matchWest == True):
						#if the region of pixCheck is not == to region of pixNorth
						if(pix2region[str(pixNorth)] != pix2region[str(pixCheck)]):
							pix2region[str(pixCheck)] = minReg(pix2region[str(pixNorth)], pix2region[str(pixWest)])
							uf.union(str(pix2region[str(pixNorth)]), str(pix2region[str(pixWest)]))
					elif(matchWest == False):
						pix2region[str(pixCheck)] = pix2region[str(pixNorth)]
			
			if(matchWest == False and matchNorth == False):
				uf.insert_objects(str(regionCnt))
				pix2region[str(pixCheck)] = regionCnt
				regionCnt += 1
				
	'''	Pass Two   '''
	print "Pass Two"
	for y in range(img.height):
		for x in range(img.width):
			pixCheck = [y, x]
			#get the address of the pixel to compare to
			regInt = pix2region[str(pixCheck)]
			parReg = uf.find(str(regInt))
			pix2region[str(pixCheck)] = int(parReg)
			if(not region2pix.has_key(parReg)):
				region2pix[parReg] = []
			region2pix[parReg].append(pixCheck)
					
	print "coloring regions"
	blobImg = cv.CreateImage((320, 240), cv.IPL_DEPTH_8U, 3)
	for key in region2pix.keys():
		avgColor = getAvgColor(region2pix[key], img)
		region2color[key] = avgColor
		for i in range(len(region2pix[key])):
			blobImg[region2pix[key][i][0], region2pix[key][i][1]] = avgColor
				
	return blobImg, region2color, region2pix
			
			
def getAvgColor(pixList, img):
	blue = 0
	green = 0
	red = 0
	
	for i in range(len(pixList)):
		rgb = img[pixList[i][0], pixList[i][1]]
		blue += rgb[0]
		green += rgb[1]
		red += rgb[2]
		
	blueAvg = blue / len(pixList)
	greenAvg = green / len(pixList)
	redAvg = red / len(pixList)
	
	return (int(blueAvg), int(greenAvg), int(redAvg))
				
def getPixOffset(pixIn, pixComp, img):
	pixCompReal = []
	pixCompReal.append(pixIn[0] + pixComp[0])
	pixCompReal.append(pixIn[1] + pixComp[1])
		
	if(pixCompReal[0] < 0 or pixCompReal[0] >= img.height \
		or pixCompReal[1] < 0 or pixCompReal[1] >= img.width):
		pixCompReal[0] = pixIn[0]
		pixCompReal[1] = pixIn[1] 
	#print pixCompReal
	return pixCompReal

def checkPixels(pixIn, pixComp, img, threshold):
	pixInVal = img[pixIn[0], pixIn[1]]
	pixCompVal = img[pixComp[0], pixComp[1]]
	
	blueDiff = abs(pixInVal[0] - pixCompVal[0])
	greenDiff = abs(pixInVal[1] - pixCompVal[1])
	redDiff = abs(pixInVal[2] - pixCompVal[2])
	
	if(blueDiff < threshold and redDiff < threshold and greenDiff < threshold):
		return True
	else:
		return False
	
	#~ avgDiff = (blueDiff + greenDiff + redDiff) / 3
	#~ 
	#~ return avgDiff


def minReg(reg1, reg2):
	if(reg1 <= reg2):
		return reg1
	else:
		return reg2
		
		
def inList(key, list):
	for i in range(len(list)):
		if(key == list[i]):
			return True
	return False
if __name__ == '__main__':
	main()

