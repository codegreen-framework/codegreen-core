from codegreen_core.utilities.message import CodegreenDataError, Message
from datetime import datetime, timezone, timedelta
import codegreen_core.tools.loadshift_time as ts
import pandas as pd
import pytz

try:
  a,b,c, = ts.predict_now("DE",12,0,datetime(2024,10,30,23,00,00))
except Exception as  e:
  print(e)


#print(a,b,c)