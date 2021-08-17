#-*-coding:utf-8-*-
import sys
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLabel, QMainWindow, QPushButton, QApplication, QComboBox, QProgressBar, qApp
from urllib.request import urlopen
from bs4 import BeautifulSoup as soup

class BundesligaBetAdvisor(QMainWindow):
    def __init__(self):
        super().__init__()

        ### load UI layout
        uic.loadUi('betadvisor.ui', self)
        self.setWindowTitle('Bundesliga Bet Advisor')
        self.setWindowIcon(QIcon('betadvisor.ico'))

        ### connect Buttons, Boxes, Labels, etc.
        self.matchDay = self.findChild(QComboBox, 'comboBoxMatchday')

        self.buttonMatches = self.findChild(QPushButton, 'pushButtonMatches')
        self.buttonMatches.clicked.connect(self.get_matches)

        self.comboBoxStart = self.findChild(QComboBox, 'comboBoxSeasonStart')
        self.comboBoxEnd = self.findChild(QComboBox, 'comboBoxSeasonEnd')

        self.buttonSearch = self.findChild(QPushButton, 'pushButtonSearch')
        self.buttonSearch.clicked.connect(self.get_results)

        self.progress = self.findChild(QProgressBar, 'progressBar')

        ### execute initial methods to set up layout
        self.make_matchday_list()
        self.make_season_list()
        self.progress.setValue(0)


    def make_matchday_list(self):
        for i in range(1,35):
            self.matchDay.addItem('%d. Matchday' %i)

    def make_season_list(self):
        for i in range(10,21):
            self.comboBoxStart.addItem('%02d/%02d' %(i, i+1))
            self.comboBoxEnd.addItem('%02d/%02d' % (i, i + 1))

    def make_season_strings(self):
        start, _ = self.comboBoxStart.currentText().split('/')
        _, end = self.comboBoxEnd.currentText().split('/')

        seasons = []
        for i in range(int(start), int(end)):
            season = '20%02d-%02d' %(i, i+1)
            seasons.append(season)
        return seasons

    def get_matches(self):
        self.matches = {}
        num_matchday = int(self.matchDay.currentText().split('.')[0])
        myurl = 'https://www.kicker.de/bundesliga/spieltag/2021-22/%d' %(num_matchday)
        uClient = urlopen(myurl)
        page_html = uClient.read()
        uClient.close()

        page_soup = soup(page_html, "html.parser")
        containers = page_soup.findAll("div", {"class": "kick__v100-gameList__gameRow__gameCell"})
        count = 1
        for i,container in enumerate(containers):
            team1, team2 = [t.text.strip() for t in container.findAll("div", {"class": "kick__v100-gameCell__team__shortname"})]
            self.findChild(QLabel, 'label_%d' %(count)).setText(team1)
            count += 1
            self.findChild(QLabel, 'label_%d' % (count)).setText(team2)
            count += 1
            self.findChild(QLabel,'result_%d' %(i+1)).setText('average result not available')
            self.matches['match_%d' %(i+1)] = {}
            self.matches['match_%d' % (i+1)]['teams'] = [team1, team2]
            self.matches['match_%d' % (i+1)]['goalsHome'] = 0
            self.matches['match_%d' % (i+1)]['goalsAway'] = 0
            self.matches['match_%d' % (i+1)]['matchCounts'] = 0

            self.findChild(QComboBox,'comboBox_%d' %(i+1)).clear()

    def get_results(self):
        seasons = self.make_season_strings()
        mdays = range(1,35)
        self.progress.setMaximum(len(mdays) * len(seasons))
        c = 0
        for season in seasons:
            for md in mdays:
                myurl = 'https://www.kicker.de/bundesliga/spieltag/%s/%s' %(season, md)

                uClient = urlopen(myurl)
                page_html = uClient.read()
                uClient.close()

                page_soup = soup(page_html, "html.parser")
                containers = page_soup.findAll("div", {"class": "kick__v100-gameList__gameRow__gameCell"})

                for container in containers:
                    team1, team2 = [t.text.strip() for t in container.findAll("div", {"class": "kick__v100-gameCell__team__shortname"})]
                    for key in self.matches.keys():
                        teams = self.matches[key]['teams']
                        match_num = str(key).split('_')[-1]
                        if team1 in teams and team2 in teams:
                            score1, score2 = [s.text.strip() for s in container.findAll("div", {"class": "kick__v100-scoreBoard__scoreHolder__score"})][:2]

                            self.findChild(QComboBox, 'comboBox_%s'%(match_num)).addItem('Matchday %02d in Season %s: %s - %s %s:%s' %(md, season.replace('-', '/'), team1, team2,score1,score2))
                            if team1 == teams[0]:
                                self.matches[key]['goalsHome'] += int(score1)
                                self.matches[key]['goalsAway'] += int(score2)
                            else:
                                self.matches[key]['goalsHome'] += int(score2)
                                self.matches[key]['goalsAway'] += int(score1)
                            self.matches[key]['matchCounts'] += 1
                c += 1
                self.progress.setValue(c)
                qApp.processEvents()
                print('Scraping kicker.de for results @ Matchday %02d of Season %s' %(md, season.replace('-', '/')))
        for key in self.matches.keys():
            if self.matches[key]['matchCounts'] > 0:
                ave_goals1 = self.matches[key]['goalsHome'] / self.matches[key]['matchCounts']
                ave_goals2 = self.matches[key]['goalsAway'] / self.matches[key]['matchCounts']
                num = str(key).split('_')[-1]
                self.findChild(QLabel, 'result_%s' % (num)).setText('average - %.1f : %.1f' %(ave_goals1, ave_goals2))

### Execute program
def main():
    app = QApplication(sys.argv)
    window = BundesligaBetAdvisor()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()