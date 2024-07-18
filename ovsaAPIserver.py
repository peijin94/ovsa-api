from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import os
import json

app = FastAPI()

# File path
file_path = "./data/EOVSA_flare_list_from_wiki.csv"

# Load the CSV data
if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file {file_path} does not exist.")

# Load CSV with all columns as strings and replace NaN with empty string
df = pd.read_csv(file_path, dtype=str).fillna("")

# Convert Date and Time columns to datetime for filtering
df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time (UT)'])

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, float, int)):
            return str(obj)
        elif isinstance(obj, np.bool_):
            return str(bool(obj))
        elif pd.isna(obj):
            return ""
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(obj):
    return json.dumps(obj, cls=CustomJSONEncoder)

@app.get("/query_flares")
async def query_flares(
    instr: str = Query(..., description="Instrument"),
    type: str = Query(..., description="Query type"),
    t0: str = Query(..., description="Start time"),
    t1: str = Query(..., description="End time"),
    flare_class: Optional[List[str]] = Query(None, description="Flare classes to include")
):
    if instr.lower() != "eovsa" or type.lower() != "flarelist":
        return JSONResponse(content={"error": "Invalid instrument or query type"}, status_code=400)

    try:
        start_time = pd.to_datetime(t0)
        end_time = pd.to_datetime(t1)
    except ValueError:
        return JSONResponse(content={"error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, status_code=400)

    # Filter by time range
    mask = (df['datetime'] >= start_time) & (df['datetime'] <= end_time)
    
    # Filter by flare class if specified
    if flare_class:
        class_mask = df['flare_class'].apply(lambda x: any(c.upper() in x.upper() for c in flare_class))
        mask = mask & class_mask

    result = df[mask].to_dict(orient='records')
    
    # Remove the 'datetime' column from the result as it's not in the original CSV
    for record in result:
        record.pop('datetime', None)
    
    # Use safe_json_dumps to handle any remaining problematic values
    try:
        encoded_result = safe_json_dumps({"flares": result})
        return JSONResponse(content=json.loads(encoded_result))
    except Exception as e:
        print(f"Error encoding response: {str(e)}")
        print(f"Problematic result: {result}")
        return JSONResponse(content={"error": f"Error encoding response: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)