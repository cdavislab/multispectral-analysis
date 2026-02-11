import pytest
from msagui.model.metadata import ImageMeta, MetadataStore

def test_add_and_keys():
    store = MetadataStore()
    meta1 = ImageMeta(key="1", group="A", kind="input")
    meta2 = ImageMeta(key="2", group="B", kind="processed")
    store.add(meta1)
    store.add(meta2)
    assert store.keys == ["1", "2"]

def test_basenames():
    store = MetadataStore()
    meta1 = ImageMeta(key='1',nickname="/path/to/image1.tif", group="A", kind="input")
    meta2 = ImageMeta(key='2',nickname="/another/path/image2.jpg", group="B", kind="processed")
    store.add(meta1)
    store.add(meta2)
    assert store.basenames == ["image1", "image2"]

def test_delete():
    store = MetadataStore()
    meta1 = ImageMeta(key="1", group="A", kind="input")
    meta2 = ImageMeta(key="2", group="B", kind="processed")
    store.add(meta1)
    store.add(meta2)
    store.delete("1")
    assert store.keys == ["2"]
    store.delete("2")
    assert store.keys == []

def test_by_group():
    store = MetadataStore()
    meta1 = ImageMeta(key="1", group="A", kind="input")
    meta2 = ImageMeta(key="2", group="B", kind="processed")
    meta3 = ImageMeta(key="3", group="A", kind="input")
    store.add(meta1)
    store.add(meta2)
    store.add(meta3)
    group_a = store.by_group("A")
    assert len(group_a) == 2
    assert all(m.group == "A" for m in group_a)

def test_new_key():
    store = MetadataStore()
    assert store.new_key() == "1"
    store.add(ImageMeta(key="1", group="A", kind="input"))
    assert store.new_key() == "2"
    store.add(ImageMeta(key="2", group="A", kind="input"))
    store.add(ImageMeta(key="4", group="A", kind="input"))
    assert store.new_key() == "3"

def test_change_keyword():
    store = MetadataStore()
    meta = ImageMeta(key="1", group="A", kind="input", keyword="old")
    store.add(meta)
    store.change_keyword("1", "new")
    assert store.items[0].keyword == "new"

def test_change_group():
    store = MetadataStore()
    meta = ImageMeta(key="1", group="A", kind="input")
    store.add(meta)
    store.change_group("1", "B")
    assert store.items[0].group == "B"

def test_statistics_optional():
    meta = ImageMeta(key="1", group="A", kind="input")
    assert meta.statistics is None
    meta2 = ImageMeta(key="2", group="A", kind="input", statistics={"mean": 1.0})
    assert meta2.statistics == {"mean": 1.0}