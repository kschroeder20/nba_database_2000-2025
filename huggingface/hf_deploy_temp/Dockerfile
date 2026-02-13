FROM python:3.11-slim

# Install datasette and useful plugins
RUN pip install --no-cache-dir \
    datasette==0.64.8 \
    datasette-cluster-map \
    datasette-vega

WORKDIR /app

COPY nba.db .
COPY metadata.json .

# Expose port 7860 (for HF)
EXPOSE 7860

# Run datasette
CMD ["datasette", "nba.db", \
     "--metadata", "metadata.json", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--cors", \
     "--setting", "sql_time_limit_ms", "3500", \
     "--setting", "max_returned_rows", "10000"]
