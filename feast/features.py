from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32

iris_entity = Entity(name="iris_id")

iris_source = FileSource(
    name="iris_features_source",
    path="../data/processed/features.parquet",
    timestamp_field="event_timestamp",
)

iris_features = FeatureView(
    name="iris_features",
    entities=[iris_entity],
    ttl=timedelta(days=365),
    schema=[
        Field(name="sepal_length", dtype=Float32),
        Field(name="sepal_width", dtype=Float32),
        Field(name="petal_length", dtype=Float32),
        Field(name="petal_width", dtype=Float32),
    ],
    online=True,
    source=iris_source,
)
