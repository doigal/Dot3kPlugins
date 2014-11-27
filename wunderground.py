import json
import subprocess
import linecache
import time
from time import sleep

from dot3k.menu import MenuOption
import dot3k.backlight

#The Wunderground API limit is 500 per day and 10 per minute for free accounts. To be safe limit the updates to every 30 minutes.
updateinterval = 1800
    
def run_cmd(cmd):
   p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
   output = p.communicate()[0]
   return output

class WU_Weather(MenuOption):
#Returns the current weather for the desired station
  def __init__(self):
    self.last = self.millis()
    self.last_update = 0
    
    self.apikey = 'MissingAPI'
    self.stations = 'MissingStat'

    self.weatherconditionsresult = ''

    self.is_setup = False
        
    MenuOption.__init__(self)
    
  def setup(self, config):
    MenuOption.setup(self, config)
    self.load_options()       
    
  def load_options(self):
    self.apikey    = self.get_option('Wunderground','wuapikey', self.apikey)
    self.stations  = self.get_option('Wunderground','wustations',','.join(self.stations)).split(',')
      
  def weatherconditions(self):
    weathercond = "curl -s http://api.wunderground.com/api/" + self.apikey + "/conditions/q/" + self.stations[0] + ".json | grep -E 'full|temp_c|windchill_c|humidity|wind_dir|wind_kph|visibility|weather'"
  
    weathercondresult = run_cmd (weathercond)
    
    w_location = weathercondresult.split("\n\t\t")[1].split("\"")[3]						# Location
    w_conditions = weathercondresult.split("\n\t\t")[3].split("\"")[3]						# Conditions 
    w_acttemp = weathercondresult.split("\n\t\t")[4].split("\"")[2].split(":")[1][:-1]		# Actual Temp
    w_humidty = weathercondresult.split("\n\t\t")[5].split("\"")[3]							# Humidity
    w_winddir = weathercondresult.split("\n\t\t")[6].split("\"")[3]							# Wind Dir
    w_windspd = weathercondresult.split("\n\t\t")[7].split("\"")[2].split(":")[1][:-1]		# Wind spd (KPH)
    w_windchill = weathercondresult.split("\n\t\t")[8].split("\"")[3]						# Wind chill factor
    w_vis = weathercondresult.split("\n\t\t")[10].split("\"")[3]							# Visibility
    
    return w_location, w_conditions, w_acttemp, w_humidty, w_winddir, w_windspd, w_windchill, w_vis
    
  def redraw(self, menu, force = False):

    if not self.is_setup:
        self.load_options()
        self.weatherconditionsresult = self.weatherconditions()
        self.lastupdate = time.strftime('%H:%M')
        self.is_setup = True

    now = self.millis()

    tdelta = self.millis() - self.last_update
    ttupdate = str((updateinterval - tdelta/1000)/60)
    
    text1 = self.weatherconditionsresult[0]
    text2 = self.weatherconditionsresult[1] + ' ' + self.weatherconditionsresult[2] + 'degC ' + self.weatherconditionsresult[3] + ' Wind: ' + self.weatherconditionsresult[4] + ' ' + self.weatherconditionsresult[5] + 'kph'
    #text3 = str(self.lastupdate + ' Next update: ' + str(updateinterval - tdelta/1000) + 's')
    #text3 = str(self.lastupdate + ' Next update: ' + str(updateinterval - tdelta/1000) + 's')
    text3 = str('Updated: ' + self.lastupdate  + ' ' + ttupdate + 'min til next update')
    
    menu.write_option(row = 0, 
       text = text1, 
       scroll=True,         		# Enable auto-scrolling
       scroll_speed=350,   		# Delay between each scroll position
       scroll_delay=5000,   		# Delay ( in ms ) until auto-scrolling starts
       scroll_repeat=30000, 		# Delay ( in ms ) before auto-scroll repeats
       scroll_padding='          '      # Padding added to the end of the text so it doesn't just wrap around onto itself
       )
    
    menu.write_option(row = 1, 
       text = text2, 
       scroll=True,        
       scroll_speed=400,   
       scroll_delay=2000,  
       scroll_repeat=100,  
       scroll_padding='          '
       )

    menu.write_option(row = 2, 
       text = text3, 
       scroll=True,         
       scroll_speed=350,    
       scroll_delay=5000,   
       scroll_repeat=15000, 
       scroll_padding='         ' 
       )       
       
    if tdelta < 1000 * updateinterval and not force:
      return False
    # Time to update!
    self.lastupdate = time.strftime('%H:%M')
    self.last_update = self.millis()
    self.weatherconditionsresult = self.weatherconditions()
    
class WU_Suntimes(MenuOption):
# Gets the sunrise and sunset times and the Moon phase. 
# As this is data dosnt change very often, it updates every time you enter rather than on the update interval.

  def __init__(self):
    self.last = self.millis()
    self.last_update = 0
    
    self.apikey = 'MissingAPI'
    self.stations = 'MissingStat'
    
    self.WU_Suntimes_Result = ''
    
    self.is_setup = False
    
    MenuOption.__init__(self)

  def setup(self, config):
    MenuOption.setup(self, config)
    self.load_options()       
    
  def load_options(self):
    self.apikey    = self.get_option('Wunderground','wuapikey', self.apikey)
    self.stations  = self.get_option('Wunderground','wustations',','.join(self.stations)).split(',')

  def wu_astro(self):
    weatherastro = "curl -s http://api.wunderground.com/api/" + self.apikey + "/astronomy/geolookup/pws:0/q/" + self.stations[0] + ".json | grep -E 'city|hour|minute|percentIlluminated|phaseofMoon' | grep -v { "
    weatherastroresult = run_cmd (weatherastro)
    
    w_astro_location    = weatherastroresult.split("\n\t\t")[0].split("\"")[3]
    w_astro_moonpercent = weatherastroresult.split("\n\t\t")[1].split("\"")[3] 
    w_astro_moonphase   = weatherastroresult.split("\n\t\t")[2].split("\"")[3]
    w_astro_sunrise     = weatherastroresult.split("\n\t\t")[5].split("\"")[3] + ":" + weatherastroresult.split("\n\t\t")[6].split("\"")[3]
    w_astro_sunset      = weatherastroresult.split("\n\t\t")[7].split("\"")[3] + ":" + weatherastroresult.split("\n\t\t")[8].split("\"")[3]
   
    return w_astro_location, w_astro_sunrise, w_astro_sunset, w_astro_moonpercent, w_astro_moonphase
     
  def redraw(self, menu):
    if not self.is_setup:
        self.load_options()
        self.WU_Suntimes_Result = self.wu_astro()
        self.is_setup = True

 
    menu.write_row(0,self.WU_Suntimes_Result[0])
    
    text1 = str('Sunrise: ' + self.WU_Suntimes_Result[1] + ' Sunset: ' + self.WU_Suntimes_Result[2])
    text2 = str('Moon: ' + self.WU_Suntimes_Result[4] + '. Illuminated: ' + self.WU_Suntimes_Result[3] + '%')
       
    menu.write_option(row = 1, 
       text =text1, 
       scroll=True,         
       scroll_speed=500,    
       scroll_delay=1000,
       scroll_repeat=15 * 1000, 
       scroll_padding='          '
       )    
    
    menu.write_option(row = 2, 
       text = text2, 
       scroll=True,     
       scroll_speed=500,
       scroll_delay=1000,
       scroll_repeat=15 * 1000, 
       scroll_padding='          '  
       )      
    
    
    
class WU_Alerts(MenuOption):
# Gets the current alerts. 

  def __init__(self):
    self.last = self.millis()
    self.last_update = 0
    
    self.apikey = 'MissingAPI'
    self.stations = 'MissingStat'
    
    self.WU_Alerts_Result = ''
    
    self.is_setup = False
    
    MenuOption.__init__(self)

  def setup(self, config):
    MenuOption.setup(self, config)
    self.load_options()       
    
  def load_options(self):
    self.apikey    = self.get_option('Wunderground','wuapikey', self.apikey)
    self.stations  = self.get_option('Wunderground','wustations',','.join(self.stations)).split(',')

  def wu_alerts(self):
    weatheralerts = "curl -s http://api.wunderground.com/api/" + self.apikey + "/alerts/geolookup/pws:0/q/" + self.stations[0] + ".json | grep -E 'city|wtype_meteoalarm_name|level_meteoalarm_name|message|date|expires' | grep -v { | grep -v attribution "
    weatheralertsresult = run_cmd (weatheralerts)
    
    try:
       w_alert_location   = weatheralertsresult.split("\n\t\t")[0].split("\"")[3]  
       w_alert_type       = weatheralertsresult.split("\n\t\t")[1].split("\"")[3] 
       w_alert_level      = weatheralertsresult.split("\n\t\t")[2].split("\"")[3]
       w_alert_timestart  = weatheralertsresult.split("\n\t\t")[3].split("\"")[3]
       w_alert_timeend    = weatheralertsresult.split("\n\t\t")[5].split("\"")[3]
       w_alert_message    = weatheralertsresult.split("\n\t\t")[7].split("\"")[3]
    except:
       w_alert_location   = weatheralertsresult.split("\n\t\t")[0].split("\"")[3]         
       w_alert_type       = 'No Current Alert'
       w_alert_level      = ''
       w_alert_timestart  = ''
       w_alert_timeend    = ''
       w_alert_message    = ''
       
    return w_alert_location, w_alert_type, w_alert_level, w_alert_timestart, w_alert_timeend, w_alert_message
     
  def redraw(self, menu):
    if not self.is_setup:
        self.load_options()
        self.WU_Alert_Result = self.wu_alerts()
        self.is_setup = True
 
    menu.write_row(0,self.WU_Alert_Result[0])
    
    if self.WU_Alert_Result[1] == 'No Current Alert':
       text1 = self.WU_Alert_Result[1]
       text2 = ''
    else:
       text1 = self.WU_Alert_Result[1] + ': ' + self.WU_Alert_Result[2]
       text2 = 'Valid ' + self.WU_Alert_Result[3] + ' to ' + self.WU_Alert_Result[4] + ' ' +  self.WU_Alert_Result[5]
    
   
    menu.write_option(row = 1, 
       text =text1, 
       scroll=True,         
       scroll_speed=500,    
       scroll_delay=1000,
       scroll_repeat=15 * 1000, 
       scroll_padding=' '
       )    
    
    menu.write_option(row = 2, 
       text = text2, 
       scroll=True,     
       scroll_speed=500,
       scroll_delay=1000,
       scroll_repeat=15 * 1000, 
       scroll_padding='          '  
       )      
       
class WU_Fcst(MenuOption):
# Gets the 3 Day forecast. 

  def __init__(self):
    self.last = self.millis()
    self.last_update = 0
    self.modes = ['P1','P2','P3','P4','P5','P6','P7','P8']
    self.mode = 0
    
    self.apikey = 'MissingAPI'
    self.stations = 'MissingStat'
    
    self.WU_Fcst_Result = ''
    
    self.is_setup = False
    
    MenuOption.__init__(self)

  def setup(self, config):
    MenuOption.setup(self, config)
    self.load_options()       
    
  def load_options(self):
    self.apikey    = self.get_option('Wunderground','wuapikey', self.apikey)
    self.stations  = self.get_option('Wunderground','wustations',','.join(self.stations)).split(',')

  def wu_fcst(self):
    weatherforecast = "curl -s http://api.wunderground.com/api/" + self.apikey + "/forecast/geolookup/pws:0/q/" + self.stations[0] + ".json | grep -E 'city|title|fcttext_metric' | grep -v { "
    weatherforecastresult = run_cmd (weatherforecast)
    
    w_fcst_location   = weatherforecastresult.split("\n\t\t")[0].split("\"")[3]
    
    w_fcst_title      = [weatherforecastresult.split("\n\t\t")[1].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[3].split("\"")[3], 
                        weatherforecastresult.split("\n\t\t")[5].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[7].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[9].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[11].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[13].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[15].split("\"")[3]]

    w_fcst_text       = [weatherforecastresult.split("\n\t\t")[2].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[4].split("\"")[3], 
                        weatherforecastresult.split("\n\t\t")[6].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[8].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[10].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[12].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[14].split("\"")[3],
                        weatherforecastresult.split("\n\t\t")[16].split("\"")[3]]

    return w_fcst_location, w_fcst_title, w_fcst_text

  def up(self):
    self.mode = (self.mode - 1) % len(self.modes)
    return True

  def down(self):
    self.mode = (self.mode + 1) % len(self.modes)
    return True

  def redraw(self, menu):
    if not self.is_setup:
        self.load_options()
        self.WU_Fcst_Result = self.wu_fcst()
        self.is_setup = True
 
    w_fcst_title_local = self.WU_Fcst_Result[1]
    w_fcst_text_local = self.WU_Fcst_Result[2]

    menu.write_row(0,self.WU_Fcst_Result[0])
    menu.write_row(1,w_fcst_title_local[self.mode])
    #menu.write_row(2,'')
    

    
    #print w_fcst_title_local[1]
    #print w_fcst_text_local [1]
    
   
    #menu.write_option(row = 1, 
    #   text =text1, 
    #   scroll=True,         
    #   scroll_speed=500,    
    #   scroll_delay=1000,
    #   scroll_repeat=15 * 1000, 
    #   scroll_padding=' '
    #   )    
    
    menu.write_option(row = 2, 
       text = w_fcst_text_local [self.mode], 
       scroll=True,     
       scroll_speed=500,
       scroll_delay=1000,
       scroll_repeat=15 * 1000, 
       scroll_padding='          '  
       )      
       
