# this code is not yet used
from codegreen_core.models import predict
from codegreen_core.data import energy
from datetime import datetime

e = energy("SE", datetime(2024, 1, 2), datetime(2024, 1, 3))["data"]
# print(e)
forecasts = predict.run("SE", e)
print(forecasts)
