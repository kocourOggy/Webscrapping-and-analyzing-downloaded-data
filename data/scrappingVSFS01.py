import requests
import time
import sys
import webbrowser
from bs4 import BeautifulSoup as Soup

globalRequest = {
	'agenda' : 'th',
	'FAK' : '6410',
	'PRI' : '-',
	'ROK' : '2017',
	'TIT' : 'Bc.',
	'PRA' : '-',
	#'search' : 'Vyhledat'
	'vypsat' : '1',
	'exppar' : '1',
	'por' : '51'
}

URL_WITH_ADDITIONAL_INFO = "https://is.vsfs.cz"


def extractSearchingParam(soupPage):
	arrayOfParam = []
	dOrigin = {'exppar':'1', 'por':'1'}
	array = soupPage.find("div", {"style":"margin: 9px;"}).find_all('a')

	if ( array[0].get('href') == '#' ):
		arrayOfParam.append(dOrigin)
		return arrayOfParam

	for param in array:
		paramArray = param.get('href').split(';')
		por = paramArray[-1].split('=')[-1]
		exppar = paramArray[-2].split('=')[-1]

		dCopy = dOrigin.copy()
		dCopy['por'] = por
		dCopy['exppar'] = exppar
		arrayOfParam.append(dCopy)

	return arrayOfParam


def processThesis(thesis, fileObject):
	global URL_WITH_ADDITIONAL_INFO, globalRequest

	thesisInfo = thesis.find_all("i")
	if (len(thesisInfo) > 7):
		possibleName = thesisInfo[0]
		nameConvert = ''
		for letter in possibleName:
			nameConvert += str(letter)
		if ( "roz." in nameConvert ):
			print("Roz. problem")
			del thesisInfo[0]

	if ( len(thesisInfo) != 7 ):
		print("Bad number of data len: ", len(thesisInfo))

	year = extractYearFromList(thesisInfo)
	successRate = extractSuccessRateFromList(thesisInfo)

	extraLink = extractLink(thesis)

	#print("url: " + URL_WITH_ADDITIONAL_INFO + extraLink)

	requestForPage = handleRequestGET(URL_WITH_ADDITIONAL_INFO + extraLink, 3)
	if requestForPage.status_code != 200:
		print("Cannot handle request with status code: ", requestForPage.status_code)
		time.sleep(10)
		fileObject.close()
		return

	soupWebPage = Soup(requestForPage.content, "html5lib")

	authorName = soupWebPage.h3.b.string
	nameOfThesis = soupWebPage.find_all('h2')[1].string

	subjectOfStudy = soupWebPage.find('div', {'class':'oddil'}).em.string.split('/')[1]
	typeOfThesis = globalRequest['TIT']

	nameOfSupervisor = extractSupervisor(soupWebPage)
	nameOfOponent = extractOponent(soupWebPage)

	authorName = authorName.replace(',', ' ')
	nameOfThesis = nameOfThesis.replace(',', ' ')
	subjectOfStudy = subjectOfStudy.replace(',', ' ')
	nameOfSupervisor = nameOfSupervisor.replace(',', ' ')
	nameOfOponent = nameOfOponent.replace(',', ' ')

	'''
	print("author: " +  authorName)
	print("year: " +  year)
	print("type of thesis:" + typeOfThesis)
	print("subjectOfStudy: " +  subjectOfStudy)
	print("nameOfThesis: " +  nameOfThesis)
	print("succes: " +  successRate)
	print("supervisor: " +  nameOfSupervisor)
	print("oponent: " +  nameOfOponent)
	'''

	csvRow = authorName+','+nameOfThesis+','+subjectOfStudy+','+typeOfThesis+','+year+','+successRate+','+nameOfSupervisor+','+nameOfOponent+'\n'
	'''
	print("author: "+authorName+"; year: "+year+"; supervisor: "+nameOfSupervisor+"; oponent: "+nameOfOponent)
	print("nameOfThesis: "+nameOfThesis+"; subjectOfStudy: "+subjectOfStudy)
	print("Succes: "+successRate)
	'''
	if len(csvRow.split(',')) == 8:
		fileObject.write(csvRow)
		print("Succesful write to CSV file")
	else:
		print("Bad CSV format!!!")


def checkRequest(requestForPage):
	if requestForPage.status_code != 200:
		captchaPageSoup = Soup(requestForPage.content, "html5lib")
		captchaPage = captchaPageSoup.find_all('a')[5].get('href')

		print("Go to the folowing page and resolve a captcha code:")
		print(URL_WITH_ADDITIONAL_INFO + captchaPage)
		print()
		webbrowser.open(URL_WITH_ADDITIONAL_INFO + captchaPage)
		
		time.sleep(5)
		print("remain 10 seconds...")
		time.sleep(10)
		return False

	return True


def handleRequestGET(urlString, nAttempts):
	for i in range(nAttempts):
		requestForPage = requests.get(urlString)
		isRequestOK = checkRequest(requestForPage)
		if (isRequestOK == True):
			break
	return requestForPage


def handleRequestPOST(urlString, myRequest, nAttempts):
	for i in range(nAttempts):
		requestForPage = requests.post(urlString, myRequest)
		isRequestOK = checkRequest(requestForPage)
		if (isRequestOK == True):
			break
	return requestForPage



def extractName(thesis):
	rawName = thesis.find("b").string
	rawName = rawName.replace(',', '')
	return rawName

def extractYearFromList(thesisInfo):
	year = thesisInfo[1].string
	return year

def extractSubjectOfStudyFromList(thesisInfo):
	subjectOfStudy = thesisInfo[5].string
	return subjectOfStudy

def extractSuccessRateFromList(thesisInfo):
	success = thesisInfo[2].string
	succesList = success.split(" ")
	if "úspěšně" in succesList:
		return "1"
	elif "neúspěšně" in succesList:
		return "0"
	else:
		return "-1"

def extractNameOfThesisFromList(thesisInfo):
	nameOfThesis = thesisInfo[6].string
	return nameOfThesis

def extractLink(thesis):
	extralink = thesis.find("a")["href"]
	return extralink

def extractSupervisor(htmlPage):
	infoAbouSupervisor = htmlPage.find_all('ul')[4].find('li').string.split(', ')
	rawName = infoAbouSupervisor[0]
	return rawName

def extractOponent(htmlPage):
	infoAbouSupervisor = htmlPage.find_all('ul')[5].find('li').string.split(', ')
	rawName = infoAbouSupervisor[0]
	return rawName


def initRequestParam(additionalParam):
	global globalRequest
	globalRequest['exppar'] = additionalParam['exppar']
	globalRequest['por'] = additionalParam['por']



def extractListOfThesis(soupPage):
	listOfThesis = soupPage.find_all(style="margin-left:50px")
	return listOfThesis


def processCollectionOfThesis(listOfThesis, fileObject):
	n = 0
	for thesis in listOfThesis:
		print(n)
		print("-----------------------------------------")
		processThesis(thesis, fileObject)
		print("-----------------------------------------")
		print()
		n += 1

def openFile(filename):
	fileExists = True
	csvHead = 'Autor,Název práce,Studijní program,Typ práce,Rok,Obhájeno,Vedoucí,Oponent\n'
	try:
		tryFile = open(filename, 'r')
	except:
		fileExists = False
	else:
		tryFile.close()

	if (fileExists == False):
		csvFile = open(filename, 'a')
		csvFile.write(csvHead)
	else:
		csvFile = open(filename, 'a')

	return csvFile




def processSpecificTypeOfThesis(year, typeThesis):
	global URL_WITH_ADDITIONAL_INFO, globalRequest
	globalRequest['ROK'] = year
	globalRequest['TIT'] = typeThesis
	globalRequest['exppar'] = 1
	globalRequest['por'] = 1
	globalRequest['vypsat'] = 1

	baseURL = 'https://is.vsfs.cz/thesis/'

	csvFile = openFile(globalRequest['TIT']+globalRequest['ROK']+'.csv')

	requestForPage = handleRequestPOST(baseURL, globalRequest, 3)
	if requestForPage.status_code != 200:
		print("Cannot handle request with status code: ", requestForPage.status_code)
		time.sleep(10)
		return

	soupPage = Soup(requestForPage.text, "html5lib")
	listOfParam = extractSearchingParam(soupPage)


	for param in listOfParam:
		print("==================================")
		print('por: ', param['por'])
		print("==================================")
		initRequestParam(param)
		requestForPage = handleRequestPOST(baseURL, globalRequest, 2)

		if requestForPage.status_code != 200:
			print("Cannot handle request with status code: ", requestForPage.status_code)
			time.sleep(10)
			return

		soupPage = Soup(requestForPage.text, "html5lib")
		listOfThesis = extractListOfThesis(soupPage)

		processCollectionOfThesis(listOfThesis, csvFile)

	csvFile.close()


#========================================================
# MAIN
#========================================================

# example of usage from terminal
# -scrappingVSFS001.py 2017 Bc.
# -scrappingVSFS001.py 2016 Bc.
# -scrappingVSFS001.py 2012 Ing.

# mergin in bash:
#	head -q -n 1 Bc.2009.csv > allThesis.csv
#	tail -q -n +2 *.*.csv >> allThesis.csv

year = sys.argv[1]
typeOfThesis = sys.argv[2]
processSpecificTypeOfThesis(year, typeOfThesis)

#========================================================
# MAIN
#========================================================