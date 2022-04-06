from bs4 import BeautifulSoup as soup
from requests_html import HTMLSession
import numpy as np
import pandas as pd
import logging
import http.client


def stockCheck():
    stocks = pd.read_excel('/Users/willarcher/Desktop/myCodingStuff/StockAutomation/StockScraping.xlsx')
    tickers = stocks['Unnamed: 6'].dropna().unique()
    tickers = tickers[tickers != 'symbol']
    for ticker in tickers:
        needsUpdate = False
        print(ticker)
        checkStocks = stocks[stocks['Unnamed: 6'] == ticker]
        latestDate = [0, 0, 0]
        for idx in checkStocks.index:
            date = str(checkStocks['Unnamed: 15'][idx]).split(' ')
            if date[0] == 'nan':
                continue
            date = date[0].split('-')
            #print(date)
            if int(latestDate[0]) < int(date[0]):
                latestDate = date
                row = int(checkStocks['Unnamed: 4'][idx])
            elif int(latestDate[0]) == int(date[0]):
                if int(latestDate[1]) < int(date[1]):
                    latestDate = date
                    row = int(checkStocks['Unnamed: 4'][idx])

                elif int(latestDate[1]) == int(date[1]):
                    if int(latestDate[2]) < int(date[2]):
                        latestDate = date
                        row = int(checkStocks['Unnamed: 4'][idx])
        print(f'row: {row} date: {latestDate}')
        resp = gatherDataAndCheckForUpdate(ticker=ticker, latestDate=latestDate)
        if resp[0]:
            stocks = updateExcel(pulledData=resp[1], stocks=stocks, index=row+1)
        else:
            print('no update needed')

        
        
        
    print('completed')
def gatherDataAndCheckForUpdate(ticker, latestDate):
    pulledData = pullData(stockTicker=ticker)
    pulledMostRecQ = pulledData['mostRecentQuarter'].split('/')
    pulledMostRecQY = pulledMostRecQ[2]
    pulledMostRecQM = pulledMostRecQ[1]
    if checkMostRecQ(pulled=pulledMostRecQY, curr=latestDate[0]):
        return True, pulledData
    else:
        if checkMostRecQ(pulled=pulledMostRecQM, curr=latestDate[1]):
            return True, pulledData
    return False, pulledData



def updateExcel(pulledData, stocks, index):
    stocks['Unnamed: 16'][index] = pulledData['bookValPerShare']
    stocks['Unnamed: 17'][index] = pulledData['revenuePerShare']
    stocks['Unnamed: 18'][index] = pulledData['currentRatio']
    stocks['Unnamed: 20'][index] = pulledData['profitMargin']
    stocks['Unnamed: 21'][index] = pulledData['revenueInBillions'] 
    stocks['Unnamed: 22'][index] = pulledData['revenuePerShare']
    stocks['Unnamed: 24'][index] = pulledData['debtPerShare'] 
    stocks['Unnamed: 25'][index] = pulledData['debtToCapital']
    return stocks
    



# url = 'https://finance.yahoo.com/quote/SRE/key-statistics?p=SRE'
def checkMostRecQ(pulled, curr):
    if pulled > curr:
        return True
    return False

def convertToBill(revenue):
    if revenue[-1] == 'B':
        return float(revenue[:-1]) * 1000000000
    else:
        return float(revenue[:-1]) * 1000000
def convertDate(date):
    date = date.lower().strip().split(' ')
    #print(date)
    monthDict = {
        'jan':1,
        'feb':2,
        'mar':3,
        'apr':4,
        'may':5,
        'june':6,
        'july':7,
        'aug':8,
        'sep':9,
        'oct':10,
        'nov':11,
        'dec':12
    }
    # FIXME: POTENTIALLY CHANGE DAY TO HAVE 0 IN FRONT IF <10
    month = date[0]
    if month in monthDict.keys():
        month = monthDict[date[0]]
        year = str(date[2])[-2:]
        day = date[1][:-1]
        if month > 9:
            return f'{month}/{day}/{year}'
        else:
            return f'0{month}/{day}/{year}'
    else:
        print('error in converting date')

def pullData(stockTicker='Dont Have'):
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36'
    }   
    http.client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    print('start')
    if stockTicker == 'Dont Have':
        stockTicker = input('Enter Stock Ticker:  ')
    url = f'https://finance.yahoo.com/quote/{stockTicker.upper()}/key-statistics?p={stockTicker.upper()}'
    #url = 'https://finance.yahoo.com/quote/SRE/key-statistics?p=SRE'
    print('here1')
    s = HTMLSession()
    print('here2')
    r = s.get(url, headers=header)
    print('here3')
    r.html.render(timeout=100)
    print('here4')
    my_html = r.html._html
    print('here5')
    r.close()
    s.close()
    print('here6')
    page_soup = soup(my_html, 'html.parser')
    header = page_soup.find('div', {'id': 'quote-header-info'})
    headers = header.find_all('div')
    headerDeeper = headers[1].find('div').find('div')
    stockName = headerDeeper.find('h1').text
    navBar = page_soup.find('div', {'id': 'quote-nav'})
    navBarDeeper = navBar.find('ul')
    analysisBox = navBarDeeper.find('li', {'data-test': 'ANALYSIS'})
    analysisHREF = analysisBox.find('a')['href']
    analysisHREF = 'https://finance.yahoo.com' + analysisHREF
    stockPrice = header.find('div', class_='D(ib) Va(m) Maw(65%) Ov(h)').find('div').find('fin-streamer').text




    #navBarItems = navBar.find_all('li')



    #body = page_soup.find('div', {'id': 'YDC-Col1'})
    body = page_soup.find('div', {'id': 'Main'})
    body = body.find('div').find('div').find('div').find('section')
    body_sib = body.find('div').find_next_sibling('div').find_next_sibling('div')
    if not body_sib:
        body_sib = body.find('div', class_='Mstart(a) Mend(a)')
    valMeasures = body_sib.find('div')
    rightSide = valMeasures.find_next_sibling('div')
    leftSide = rightSide.find_next_sibling('div')
    if not valMeasures:
        valMeasures = body_sib.find('div', class_='Fl(start) smartphone_W(100%) W(100%)')
    if not rightSide:
        rightSide = body_sib.find('div', class_='Fl(end) W(50%) smartphone_W(100%)')
    if not leftSide:
        leftSide = body_sib.find('div', class_='Fl(start) W(50%) smartphone_W(100%)')
    
    deeperLeft = leftSide.find('div')
    leftTables = deeperLeft.find_all('tbody')
    if len(leftTables) == 6:
        fiscalYearRows = leftTables[0].find_all('tr')
        if len(fiscalYearRows) == 2:
            mostRecentQuarter = fiscalYearRows[1].find('td').find_next_sibling().text
        else:
            mostRecentQuarter = leftTables[0].find('td', class_='Fw(500) Ta(end) Pstart(10px) Miw(60px)')
        
        profitability = leftTables[1].find('tr')
        profitMargin = profitability.find('td').find_next_sibling().text

        incomeStatement = leftTables[3]
        revenueBox = incomeStatement.find('tr')
        revenue = revenueBox.find('td').find_next_sibling().text
        revenuePerShareBox = revenueBox.find_next_sibling()
        revenuePerShare = revenuePerShareBox.find('td').find_next_sibling().text

        balanceSheet = leftTables[4]
        balanceSheetBoxes = balanceSheet.find_all('tr')
        if len(balanceSheetBoxes) == 6:
            totalCashPerShare = balanceSheetBoxes[1].find('td').find_next_sibling().text
            totalDebt = balanceSheetBoxes[2].find('td').find_next_sibling().text
            if totalDebt[-1] == 'B':
                totalDebt = float(totalDebt[:-1]) * 1000000000
            else:
                totalDebt = float(totalDebt[:-1]) * 1000000
            
            currentRatio = balanceSheetBoxes[4].find('td').find_next_sibling().text
            bookValPerShare = balanceSheetBoxes[5].find('td').find_next_sibling().text
        else:
            print('error on balance sheet')
        cashFlowStatements = leftTables[5].find_all('tr')
        if len(cashFlowStatements) == 2:
            operatingCashFlow = cashFlowStatements[0].find('td').find_next_sibling().text
            leveredCashFlow = cashFlowStatements[1].find('td').find_next_sibling().text
        else:
            print('error on Cash Flow Statement')
    deeperRight = rightSide.find('div')
    rightTables = deeperRight.find_all('tbody')
    if len(rightTables) == 3:
        shareStatisticsBoxes = rightTables[1].find_all('tr')
        if len(shareStatisticsBoxes) == 12:
            sharesOutstanding = shareStatisticsBoxes[2].find('td').find_next_sibling().text
        else:
            print('error finding sharesOutstanding')
    else:
        print('error on right side')
    
    estimates = get_analysis(analysisHREF)
    currentYearAvgEstimate = estimates[0]
    nextYearAvgEstimate = estimates[1]

    
    operatingCashFlow = convertToNum(operatingCashFlow)
    sharesOutstanding = convertToNum(sharesOutstanding)
    revenueInBillions = convertToBill(revenue)

    # total debt / shares outstanding
    debtPerShare = totalDebt / sharesOutstanding


    # debt per share / (share price + debt per share)
    debtToCapital = debtPerShare / (float(stockPrice) + float(debtPerShare))


    #print(f'operating cash flows: {ocf}')
    #print(f'shares outstanding: {sharesOutstanding}')
    #print(f'operation cash flow per share: {ocf / sharesOutstanding}')
    # print(f'\n{stockName}\n')
    # print(f'Most Recent Quarter: {mostRecentQuarter}')
    # print(f'Profit Margin: {profitMargin}')
    # print(f'Revenue: {revenue}')
    # print(f'Revenue Per Share: {revenuePerShare}')
    # print(f'Total Cash Per Share: {totalCashPerShare}')
    # print(f'Total Debt: {totalDebt}')
    # print(f'Current Ratio: {currentRatio}')
    # print(f'Book Value Per Share: {bookValPerShare}')
    # print(f'Operating Cash Flow: {operatingCashFlow}')
    # print(f'Levered Cash Flow: {leveredCashFlow}')
    # print(f'Shares Outstanding: {sharesOutstanding}\n')
    # print(f'Current Year Avg Estimate: {currentYearAvgEstimate}')
    # print(f'Next Year Avg Estimate: {nextYearAvgEstimate}')
    print(mostRecentQuarter)
    mostRecentQuarter = convertDate(mostRecentQuarter)
    # print(mostRecentQuarter)
    # print('stock Name')
    # print(stockName)
    # print('most recent quarter:')
    # print(mostRecentQuarter)
    # print('profit margin:')
    # print(profitMargin)
    # print('revenue:')
    # print(revenue)
    # print('revenue per share:')
    # print(revenuePerShare)
    # print('total cash per share')
    # print(totalCashPerShare)
    # print('total debt:')
    # print(totalDebt)
    # print('current ratio')
    # print(currentRatio)
    # print('book value per share')
    # print(bookValPerShare)
    # print('operating Cash Flow:')
    # print(operatingCashFlow)
    # print('sharesOutstanding:')
    # print(sharesOutstanding)
    # print('debt per share:')
    # print(debtPerShare)
    # print('debt to capital:')
    # print(debtToCapital)
    profitMargin = profitMargin[:-1]

    df = pd.DataFrame({'stockName': [stockName], 'mostRecentQuarter': [mostRecentQuarter], 'profitMargin': [profitMargin], 'revenue': [revenue], 'revenuePerShare': [revenuePerShare], 'totalCashPerShare': [totalCashPerShare], 'totalDebt': [totalDebt], 'currentRatio': [currentRatio], 'bookValPerShare': [bookValPerShare], 'operatingCashFlow': [operatingCashFlow], 'leveredCashFlow': [leveredCashFlow], 'sharesOutstanding': [sharesOutstanding], 'currentYearAvgEstimate': [currentYearAvgEstimate], 'nextYearAvgEstimate': [nextYearAvgEstimate], 'revenueInBillions': [revenueInBillions], 'debtPerShare': [debtPerShare], 'debtToCapital': [debtToCapital]})
    #df.to_excel('/Users/willarcher/Desktop/StockAutomation/gatheredData.xlsx', sheet_name='NewSheet')
    #print(df)
    for i in df:
        print(f'{i}\n{df[i]}')
        print()
        print()
    # print(pd.DataFrame(data=([stockName, mostRecentQuarter, profitMargin, revenue, revenuePerShare, totalCashPerShare, totalDebt, currentRatio, bookValPerShare, operatingCashFlow, leveredCashFlow, sharesOutstanding, currentYearAvgEstimate, nextYearAvgEstimate], 1), index=['1'], columns=['stockName', 'mostRecentQuarter', 'profitMargin', 'revenue', 'revenuePerShare', 'totalCashPerShare', 'totalDebt', 'currentRatio', 'bookValPerShare', 'operatingCashFlow', 'leveredCashFlow', 'sharesOutstanding', 'currentYearAvgEstimate', 'nextYearAvgEstimate']))
    #mrqList = mostRecentQuarter.lower().strip().split(' ')
    #print(f'original date: {mostRecentQuarter}')
    #converted = convertDate(mostRecentQuarter)
    #print(f'converted date: {converted}')
    # return df



def get_analysis(url):
    print('here7')
    s = HTMLSession()
    print('here8')
    r = s.get(url)
    print('here9')
    r.html.render(timeout=100)
    print('here10')
    my_html = r.html._html
    print('here11')
    r.close()
    s.close()
    print('here12')
    page_soup = soup(my_html, 'html.parser')
    body = page_soup.find('div', {'id': 'Col1-0-AnalystLeafPage-Proxy'})
    body = body.find('section')
    analysisTable = body.find('tbody')
    tableRows = analysisTable.find_all('tr')
    cols = tableRows[1].find_all('td')
    currentYearAvgEstimate = cols[3].text
    nextYearAvgEstimate = cols[4].text

    return currentYearAvgEstimate, nextYearAvgEstimate







    
    






    # body_sibs = body.find_all('div')
    # if len(body_sibs) == 3:
    #     main = body_sibs[2]
    # else:
    #     main = body.find('div', class_='Mstart(a) Mend(a)')
    #cols = main.find_all('div')

    
    #body = body.find('div')
    #body = body.find('div')
    #body = body.find('section')

    # tables = body.find_all('tbody')
    # for table in tables:

    
    # #valuationMeasures = body.find('div', {'data-reactid': 11})
    
    
    # # rightSide = body.find('div', {'data-reactid': '201'})

    
    # # shareStatistics = rightSide.find('tbody', {'data-reactid': '268'})
    # # sharesOutstanding = shareStatistics.find('td', {'data-reactid': '289'})
    


    # leftSide = body.find('div', {'data-reactid': '433'})
    

    # fiscalYear = leftSide.find('tbody', {'data-reactid': '444'})
    # mostRecentQuarter = fiscalYear.find('td', {'data-reactid': '447'})

    # profitability = leftSide.find('tbody', {'data-reactid': '465'})
    # profitMarin = profitability.find('td', {'data-reactid': '472'}).text
    # #operatingMargin = profitability.find('td', {'data-reactid': '479'}).text
    
    # # managementEffectiveness = leftSide.find('tbody', {'data-reactid': '486'})
    # # returnOnAssets = managementEffectiveness.find('td', {'data-reactid': '493'}).text
    # # returnOnEquity = managementEffectiveness.find('td', {'data-reactid': '500'}).text
    
    # incomeStatement = leftSide.find('tbody', {'data-reactid': '507'})

    # revenue = incomeStatement.find('td', {'data-reactid': '514'}).text
    # revenuePerShare = incomeStatement.find('td', {'data-reactid': '521'}).text
    # # QuarterlyRevenueGrowth = incomeStatement.find('td', {'data-reactid': '528'}).text
    # # GrossProfit = incomeStatement.find('td', {'data-reactid': '535'}).text
    # # ebitda  = incomeStatement.find('td', {'data-reactid': '542'}).text
    # # netIncomeAviToCommon = incomeStatement.find('td', {'data-reactid': '549'}) .text
    # # dilutedEPS = incomeStatement.find('td', {'data-reactid': '556'}) .text
    # # QuarterlyEarningsGrowth = incomeStatement.find('td', {'data-reactid': '563'}).text
    
    # balanceSheet = leftSide.find('tbody', {'data-reactid': '571'})
    # #totalCash = balanceSheet.find('td', {'data-reactid': '578'}).text
    # totalCashPerShare = balanceSheet.find('td', {'data-reactid': '585'}).text
    # totalDebt = balanceSheet.find('td', {'data-reactid': '592'}).text
    # #totalDebtDivEquity = balanceSheet.find('td', {'data-reactid': '599'}).text
    # currentRatio = balanceSheet.find('td', {'data-reactid': '606'}).text
    # bookValPerShare = balanceSheet.find('td', {'data-reactid': '613'}).text


    # cashFlowStatements = leftSide.find('tbody', {'data-reactid': '620'})
    # ocf = cashFlowStatements.find('td', {'data-reactid': '627'})
    # print(f'{ocf.text}')
    # leveredCashFlow = cashFlowStatements.find('td', {'data-reactid': '627'})
    

    
    






def convertToNum(stri):
    end = stri[-1]
    start = stri[0]
    neg = False
    if start == '-':
        neg = True
        stri = stri[1:]
    if end == 'B':
        stri = float(stri[:-1])
        total = stri * 1000000000
    elif end == 'M':
        stri = float(stri[:-1])
        total = stri * 1000000
    if neg:
        total *= -1   
    return total


if __name__ == '__main__':
    pullData(stockTicker='CLR')
    #stockCheck()
