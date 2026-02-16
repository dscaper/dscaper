import pytest

from dscaper.dscaper import Dscaper
# from dscaper.dscaper_datatypes import *
import os
import tempfile
import shutil
import json
import soundfile as sf
from dscaper.dscaper_datatypes import (
    DscaperAudio,
    DscaperTimeline,
    DscaperBackground,
    DscaperEvent,
    DscaperGenerate,
    DscaperLabel,
    DscaperTimelines,
    DscaperBackgrounds,
    DscaperEvents,
    DscaperGenerations
)


@pytest.fixture
def temp_lib_base():
    temp_dir = tempfile.mkdtemp()
    print(f"*** Created temporary library base path: {temp_dir}")
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_init_creates_dirs(temp_lib_base):
    Dscaper(dscaper_base_path=temp_lib_base)
    assert os.path.exists(os.path.join(temp_lib_base, "timelines"))
    assert os.path.exists(os.path.join(temp_lib_base, "libraries"))


def test_init_raises_if_path_missing():
    with pytest.raises(FileNotFoundError):
        Dscaper(dscaper_base_path="/nonexistent/path/for/test")


def test_get_dscaper_base_path(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    assert d.get_dscaper_base_path() == temp_lib_base


def test_store_audio_and_read_audio(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Prepare dummy audio file (WAV header, not valid audio)
    # audio_bytes = b'RIFF$\x00\x00\x00WAVEfmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00' +
    # b'\x40\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    metadata = DscaperAudio(
        library="lib1",
        label="label1",
        filename="test.wav"
    )
    # Should fail on invalid audio file (non-existing file)
    resp = d.store_audio("non-existing-file.wav", metadata)
    assert resp.status == "error"
    assert resp.status_code == 404
    # Should fail on invalid audio file (length)
    invalid_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "empty_audio.wav")
    resp = d.store_audio(invalid_file, metadata)
    assert resp.status == "error"
    assert resp.status_code == 400
    # Should fail on invalid audio file (type)
    invalid_file2 = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "invalid_audio.wav")
    resp = d.store_audio(invalid_file2, metadata)
    assert resp.status == "error"
    # test storing a valid audio file
    valid_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    # valid_bytes, _ = sf.read(file_path, dtype='int16')
    # valid_bytes = valid_bytes.tobytes()  # Convert to bytes
    metadata.filename = "valid.wav"
    resp = d.store_audio(valid_file, metadata)
    # print(f"*** Response: {resp}")
    assert resp.status == "success"
    # test storing valid audio bytes
    # valid_bytes, _ = sf.read(valid_file, dtype='int16')
    # valid_bytes = valid_bytes.tobytes()  # Convert to bytes
    # metadata.filename = "valid2.wav"
    # resp = d.store_audio(valid_bytes, metadata)
    # print(f"*** Response: {resp}")
    # assert resp.status == "success"
    # add already existing audio file
    resp = d.store_audio(valid_file, metadata)
    assert resp.status == "error"
    assert resp.status_code == 400
    # update existing audio file
    resp = d.store_audio(valid_file, metadata, update=True)
    assert resp.status == "success"
    # update non-existing audio file
    metadata.filename = "non-existing.wav"
    resp = d.store_audio(valid_file, metadata, update=True)
    assert resp.status == "error"
    assert resp.status_code == 404
    # Now test reading metadata
    resp2 = d.read_audio("lib1", "label1", "valid.json")
    assert resp2.status == "success"
    # Now test reading audio
    resp3 = d.read_audio("lib1", "label1", "valid.wav")
    assert resp3.status == "success"
    assert isinstance(resp3.content, bytes)
    # test reading non-existing audio
    resp4 = d.read_audio("lib1", "label1", "non-existing.wav")
    assert resp4.status == "error"
    assert resp4.status_code == 404
    # test reading non-existing metadata
    resp5 = d.read_audio("lib1", "label1", "non-existing.json")
    assert resp5.status == "error"
    assert resp5.status_code == 404
    # test reading file with not supported extension
    test_lib_path = os.path.join(os.getcwd(), "tests", "data")
    d2 = Dscaper(dscaper_base_path=test_lib_path)
    resp6 = d2.read_audio("wrongtype", "mylabel", "audio.mp4")
    assert resp6.status == "error"


def test_store_audio_forbidden_filename(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Prepare dummy audio file (WAV header, not valid audio)
    metadata = DscaperAudio(
        library="lib1",
        label="label1",
        filename="label_metadata.wav"  # reserved filename
    )
    valid_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    resp = d.store_audio(valid_file, metadata)
    assert resp.status == "error"
    assert resp.status_code == 400


def test_get_libraries(temp_lib_base):
    test_lib_path = os.path.join(os.getcwd(), "tests", "data")
    d = Dscaper(dscaper_base_path=test_lib_path)
    # Test getting libraries
    resp = d.get_libraries()
    print(resp)
    assert resp.status == "success"
    libraries = resp.content
    assert isinstance(libraries, list)
    assert len(libraries) > 0
    assert "testlib" in libraries


def test_get_labels(temp_lib_base):
    test_lib_path = os.path.join(os.getcwd(), "tests", "data")
    d = Dscaper(dscaper_base_path=test_lib_path)
    # Test getting labels of non-existing library
    resp = d.get_labels("non-existing-lib")
    assert resp.status == "error"
    assert resp.status_code == 404
    # Test getting labels
    resp = d.get_labels("testlib")
    assert resp.status == "success"
    labels = resp.content
    assert isinstance(labels, list)
    assert len(labels) > 0
    assert "horn" in labels
    assert "horn2" in labels


def test_get_filenames(temp_lib_base):
    test_lib_path = os.path.join(os.getcwd(), "tests", "data")
    d = Dscaper(dscaper_base_path=test_lib_path)
    # Test getting filenames of non-existing library/label
    resp = d.get_filenames("non-existing-lib", "non-existing-label")
    assert resp.status == "error"
    assert resp.status_code == 404
    # Test getting filenames of non-existing label
    resp = d.get_filenames("testlib", "non-existing-label")
    assert resp.status == "error"
    assert resp.status_code == 404
    # Test getting filenames of existing library/label
    resp = d.get_filenames("testlib", "horn")
    assert resp.status == "success"
    filenames = resp.content
    print(filenames)
    print(resp)
    assert isinstance(filenames, list)
    assert len(filenames) > 0
    assert "17-CAR-Rolls-Royce-Horn.wav" in filenames
    assert "17-CAR-Rolls-Royce-Horn.json" in filenames


def test_get_file_metadata(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create and store an audio file
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="test_lib",
        label="test_label",
        filename="test_audio.wav"
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # Test getting metadata for existing file
    resp = d.get_file_metadata("test_lib", "test_label", "test_audio.wav")
    assert resp.status == "success"
    file_metadata = DscaperAudio.model_validate_json(json.dumps(resp.content))
    assert isinstance(file_metadata, DscaperAudio)
    assert file_metadata.library == "test_lib"
    assert file_metadata.label == "test_label"
    assert file_metadata.filename == "test_audio.wav"
    assert file_metadata.id is not None
    assert file_metadata.timestamp > 0
    assert file_metadata.duration > 0
    # Test getting metadata for non-existing file
    resp2 = d.get_file_metadata("test_lib", "test_label", "non_existing.wav")
    assert resp2.status == "error"
    assert resp2.status_code == 404
    # Test getting metadata for non-existing library/label
    resp3 = d.get_file_metadata("non_existing_lib", "non_existing_label", "test_audio.wav")
    assert resp3.status == "error"
    assert resp3.status_code == 404


def test_get_label_metadata(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create and store multiple audio files in the same label
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata1 = DscaperAudio(
        library="metadata_lib",
        label="metadata_label",
        filename="audio1.wav"
    )
    resp = d.store_audio(audio_file, metadata1)
    assert resp.status == "success"
    metadata2 = DscaperAudio(
        library="metadata_lib",
        label="metadata_label",
        filename="audio2.wav"
    )
    resp = d.store_audio(audio_file, metadata2)
    assert resp.status == "success"
    metadata3 = DscaperAudio(
        library="metadata_lib",
        label="metadata_label",
        filename="audio3.wav"
    )
    resp = d.store_audio(audio_file, metadata3)
    assert resp.status == "success"
    # Test getting metadata for existing label with default metadata values
    resp = d.get_label_metadata("metadata_lib", "metadata_label")
    assert resp.status == "success"
    label_metadata = DscaperLabel.model_validate_json(json.dumps(resp.content))
    assert isinstance(label_metadata, DscaperLabel)
    audio_metadata_list = label_metadata.audios
    assert isinstance(audio_metadata_list, list)
    assert len(audio_metadata_list) == 3
    # Verify each metadata entry
    filenames = []
    for audio_metadata in audio_metadata_list:
        assert isinstance(audio_metadata, DscaperAudio)
        assert audio_metadata.library == "metadata_lib"
        assert audio_metadata.label == "metadata_label"
        assert audio_metadata.id is not None
        assert audio_metadata.timestamp > 0
        filenames.append(audio_metadata.filename)
    # Check all filenames are present
    assert "audio1.wav" in filenames
    assert "audio2.wav" in filenames
    assert "audio3.wav" in filenames
    # Now set label metadata
    label_sandbox = json.dumps({"info": "test_sandbox"})
    label_metadata_to_set = DscaperLabel(
        library="metadata_lib",
        label="metadata_label",
        description="Test label description",
        sandbox=label_sandbox
    )
    resp_set = d.store_label_metadata(label_metadata_to_set)
    assert resp_set.status == "success"
    # Test getting metadata for existing label after setting metadata
    resp = d.get_label_metadata("metadata_lib", "metadata_label")
    assert resp.status == "success"
    label_metadata = DscaperLabel.model_validate_json(json.dumps(resp.content))
    assert isinstance(label_metadata, DscaperLabel)
    assert label_metadata.description == "Test label description"
    assert label_metadata.sandbox == label_sandbox
    # Test updating label metadata
    label_metadata_to_set.description = "Updated description"
    resp_update = d.store_label_metadata(label_metadata_to_set)
    assert resp_update.status == "success"
    # Test getting metadata for existing label after updating metadata
    resp = d.get_label_metadata("metadata_lib", "metadata_label")
    assert resp.status == "success"
    label_metadata = DscaperLabel.model_validate_json(json.dumps(resp.content))
    assert isinstance(label_metadata, DscaperLabel)
    assert label_metadata.description == "Updated description"
    # Test setting metadata for non-existing library/label (should create it)
    new_label_metadata = DscaperLabel(
        library="new_lib",
        label="new_label",
        description="New label description"
    )
    resp_set_new = d.store_label_metadata(new_label_metadata)
    assert resp_set_new.status == "success"
    # Test getting metadata for the newly created label
    resp = d.get_label_metadata("new_lib", "new_label")
    assert resp.status == "success"
    label_metadata = DscaperLabel.model_validate_json(json.dumps(resp.content))
    assert isinstance(label_metadata, DscaperLabel)
    assert label_metadata.description == "New label description"
    assert isinstance(label_metadata.audios, list)
    assert len(label_metadata.audios) == 0
    # Test getting metadata without audio files
    resp_no_audios = d.get_label_metadata("metadata_lib", "metadata_label", include_audios=False)
    assert resp_no_audios.status == "success"
    label_metadata_no_audios = DscaperLabel.model_validate_json(json.dumps(resp_no_audios.content))
    assert isinstance(label_metadata_no_audios, DscaperLabel)
    assert len(label_metadata_no_audios.audios) == 0
    # Test setting metadata with invalid data (missing library)
    invalid_label_metadata = DscaperLabel(
        library="",  # valid library
        label="",  # missing label
        description="Invalid label"
    )
    resp_invalid = d.store_label_metadata(invalid_label_metadata)
    assert resp_invalid.status == "error"
    # Test getting metadata for non-existing library/label
    resp2 = d.get_label_metadata("non_existing_lib", "non_existing_label")
    assert resp2.status == "error"
    assert resp2.status_code == 404


def test_create_timeline_and_list_timelines(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    props = DscaperTimeline(duration=10.0, description="desc", name="timeline1")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Check if the timeline was created
    list_resp = d.list_timelines()
    assert list_resp.status == "success"
    timelines = DscaperTimelines.model_validate_json(json.dumps(list_resp.content))
    assert isinstance(timelines, DscaperTimelines)
    assert len(timelines.timelines) > 0
    # get first timeline
    timeline = timelines.timelines[0]
    assert isinstance(timeline, DscaperTimeline)
    assert timeline.name == "timeline1"
    assert timeline.duration == 10.0
    assert timeline.description == "desc"
    assert "id" in timeline.model_dump()  # Check if ID is present
    assert "timestamp" in timeline.model_dump()  # Check if timestamp is present
    # check adding timeline with same name fails
    resp2 = d.create_timeline(props)
    assert resp2.status == "error"
    assert resp2.status_code == 400


def test_add_background_and_list_backgrounds(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=10.0, description="desc", name="timeline1")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add background
    bg = DscaperBackground(library="my_lib")
    resp = d.add_background("timeline1", bg)
    assert resp.status == "success"
    assert resp.content is not None
    bg_data = resp.content
    assert "id" in bg_data
    assert "library" in bg_data
    assert bg_data["library"] == "my_lib"
    # list backgrounds
    list_resp = d.list_backgrounds("timeline1")
    assert list_resp.status == "success"
    backgrounds = DscaperBackgrounds.model_validate_json(json.dumps(list_resp.content))
    assert isinstance(backgrounds, DscaperBackgrounds)
    assert len(backgrounds.backgrounds) > 0
    # Check if the first background has the expected properties
    background = backgrounds.backgrounds[0]
    assert isinstance(background, DscaperBackground)
    assert background.library == "my_lib"
    # add background to a non-existing timeline
    resp2 = d.add_background("non-existing-timeline", bg)
    assert resp2.status == "error"
    assert resp2.status_code == 404
    # list backgrounds of a non-existing timeline
    list_resp2 = d.list_backgrounds("non-existing-timeline")
    assert list_resp2.status == "error"
    assert list_resp2.status_code == 404


def test_add_event_and_list_events(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=10.0, description="desc", name="timeline2")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add event
    ev = DscaperEvent(library="my_lib")
    resp = d.add_event("timeline2", ev)
    assert resp.status == "success"
    assert resp.content is not None
    ev_data = resp.content
    assert "id" in ev_data
    assert "library" in ev_data
    assert ev_data["library"] == "my_lib"
    # list events
    list_resp = d.list_events("timeline2")
    assert list_resp.status == "success"
    events = DscaperEvents.model_validate_json(json.dumps(list_resp.content))
    assert isinstance(events, DscaperEvents)
    assert len(events.events) > 0
    # Check if the first event has the expected properties
    event = events.events[0]
    assert isinstance(event, DscaperEvent)
    assert event.library == "my_lib"
    assert "id" in event.model_dump()  # Check if ID is present
    assert "position" in event.model_dump()  # Check if position is present
    # add event to a non-existing timeline
    resp2 = d.add_event("non-existing-timeline", ev)
    assert resp2.status == "error"
    assert resp2.status_code == 404
    # list events of a non-existing timeline
    list_resp2 = d.list_events("non-existing-timeline")
    assert list_resp2.status == "error"
    assert list_resp2.status_code == 404


def test_generate_timeline(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=10.0, description="desc", name="timeline3")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label2",
        filename="audio2.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add background
    bg = DscaperBackground(library="my_lib")
    resp = d.add_background("timeline3", bg)
    assert resp.status == "success"
    # add events
    ev = DscaperEvent(library="my_lib", position="speakerA")
    resp = d.add_event("timeline3", ev)
    assert resp.status == "success"
    ev = DscaperEvent(library="my_lib", position="speakerB")
    resp = d.add_event("timeline3", ev)
    assert resp.status == "success"
    # add event with const label and source file
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label2"],
        source_file=["const", "audio2.wav"],
        position="speakerA"
    )
    resp = d.add_event("timeline3", ev)
    assert resp.status == "success"
    # generate timeline
    gen_props = DscaperGenerate(seed=42, ref_db=-20, reverb=0.5)
    gen_resp = d.generate_timeline("timeline3", gen_props)
    assert gen_resp.status == "success"
    assert gen_resp.content is not None
    generated_data = DscaperGenerate.model_validate(gen_resp.content)
    assert generated_data.id is not None
    assert generated_data.timestamp > 0
    assert isinstance(generated_data.generated_files, list)
    assert len(generated_data.generated_files) > 0
    # ['soundscape.wav', 'soundscape.txt', 'soundscape.jams']
    assert "soundscape.wav" in generated_data.generated_files
    assert "soundscape.txt" in generated_data.generated_files
    assert "soundscape.jams" in generated_data.generated_files
    # generate timeline with other settings
    gen_props2 = DscaperGenerate(seed=123, ref_db=-30, reverb=0.2, save_isolated_positions=True)
    gen_resp2 = d.generate_timeline("timeline3", gen_props2)
    assert gen_resp2.status == "success"
    assert gen_resp2.content is not None
    generated_data2 = DscaperGenerate.model_validate(gen_resp2.content)
    assert generated_data2.id is not None
    assert generated_data2.timestamp > 0
    assert isinstance(generated_data2.generated_files, list)
    assert len(generated_data2.generated_files) > 0
    assert "soundscape.wav" in generated_data2.generated_files
    # TODO: fix
    print("++++", generated_data2.generated_files)
    # generate none-existing timeline
    gen_resp3 = d.generate_timeline("non-existing-timeline", gen_props)
    assert gen_resp3.status == "error"
    assert gen_resp3.status_code == 404
    # get generated timelines
    gen_list_resp = d.get_generated_timelines("timeline3")
    assert gen_list_resp.status == "success"
    generated_timelines = DscaperGenerations.model_validate_json(json.dumps(gen_list_resp.content))
    assert isinstance(generated_timelines, DscaperGenerations)
    assert len(generated_timelines.generations) == 2
    # get non-existing timeline
    gen_list_resp2 = d.get_generated_timelines("non-existing-timeline")
    assert gen_list_resp2.status == "error"
    assert gen_list_resp2.status_code == 404
    # get generated timeline by ID
    gen_timeline_resp = d.get_generated_timeline_by_id("timeline3", generated_data.id)
    assert gen_timeline_resp.status == "success"
    assert gen_timeline_resp.content is not None
    # get generated timeline by non-existing ID
    gen_timeline_resp2 = d.get_generated_timeline_by_id("timeline3", "non-existing-id")
    assert gen_timeline_resp2.status == "error"
    assert gen_timeline_resp2.status_code == 404
    # get generated wav file
    gen_file_resp = d.get_generated_file("timeline3", generated_data.id, "soundscape.wav")
    assert gen_file_resp.status == "success"
    assert isinstance(gen_file_resp.content, bytes)
    # get non-existing generated wav file
    gen_file_resp2 = d.get_generated_file("timeline3", generated_data.id, "non-existing-file.wav")
    assert gen_file_resp2.status == "error"
    assert gen_file_resp2.status_code == 404
    # get generated wav file from non-existing timeline
    gen_file_resp3 = d.get_generated_file("non-existing-timeline", generated_data.id, "soundscape.wav")
    assert gen_file_resp3.status == "error"
    assert gen_file_resp3.status_code == 404
    # get generated jams file
    gen_jams_resp = d.get_generated_file("timeline3", generated_data.id, "soundscape.jams")
    assert gen_jams_resp.status == "success"
    # get generated txt file
    gen_txt_resp = d.get_generated_file("timeline3", generated_data.id, "soundscape.txt")
    assert gen_txt_resp.status == "success"
    # get generated timeline for invalid timeline folder
    test_lib_path = os.path.join(os.getcwd(), "tests", "data")
    d2 = Dscaper(dscaper_base_path=test_lib_path)
    gen_resp4 = d2.get_generated_timeline_by_id("nodata", "some_id")
    assert gen_resp4.status == "error"
    # get generated file with invalid type
    gen_file_resp4 = d2.get_generated_file("nodata", "some_id", "invalid_type.mp4")
    assert gen_file_resp4.status == "error"
    # get archive of generated files
    gen_archive_resp = d.get_generated_files("timeline3", generated_data.id)
    assert gen_archive_resp.status == "success"
    assert isinstance(gen_archive_resp.content, bytes)
    # get archive of generated files from non-existing timeline
    gen_archive_resp2 = d.get_generated_files("non-existing-timeline", generated_data.id)
    assert gen_archive_resp2.status == "error"
    assert gen_archive_resp2.status_code == 404


def test_generate_timeline_with_mp3_events(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=10.0, description="desc", name="timeline_mp3")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio (mp3)
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio_16kHz.mp3")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio_16kHz.mp3",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio_44kHz.mp3")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio_44kHz.mp3",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add specific event
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio_16kHz.mp3"],
        position="speakerA"
    )
    resp = d.add_event("timeline_mp3", ev)
    assert resp.status == "success"
    # add randomly chosen event
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"]
    )
    resp = d.add_event("timeline_mp3", ev)
    assert resp.status == "success"
    # generate timeline
    gen_props = DscaperGenerate()
    gen_resp = d.generate_timeline("timeline_mp3", gen_props)
    assert gen_resp.status == "success"
    assert gen_resp.content is not None
    generated_data = DscaperGenerate.model_validate(gen_resp.content)
    assert generated_data.id is not None


def test_generate_timeline_without_duration(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(description="desc", name="timeline4")  # no duration
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label2",
        filename="audio2.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add background
    bg = DscaperBackground(library="my_lib")
    resp = d.add_background("timeline4", bg)
    assert resp.status == "success"
    # add events
    ev = DscaperEvent(library="my_lib", label=["const", "my_label"], source_file=["const", "audio.wav"],
                      event_time=["const", "1.0"], event_duration=["const", "2.0"])
    resp = d.add_event("timeline4", ev)
    assert resp.status == "success"
    ev = DscaperEvent(library="my_lib", label=["const", "my_label"], source_file=["const", "audio.wav"],
                      event_time=["const", "5.0"], event_duration=["const", "2.0"])
    resp = d.add_event("timeline4", ev)
    assert resp.status == "success"
    # generate timeline
    gen_props = DscaperGenerate(seed=42, ref_db=-20, reverb=0.5)
    gen_resp = d.generate_timeline("timeline4", gen_props)
    assert gen_resp.status == "success"
    assert gen_resp.content is not None
    generated_data = DscaperGenerate.model_validate(gen_resp.content)
    assert generated_data.id is not None
    assert generated_data.timestamp > 0
    assert isinstance(generated_data.generated_files, list)
    assert len(generated_data.generated_files) > 0
    # ['soundscape.wav', 'soundscape.txt', 'soundscape.jams']
    assert "soundscape.wav" in generated_data.generated_files
    assert "soundscape.txt" in generated_data.generated_files
    assert "soundscape.jams" in generated_data.generated_files
    # open soundscape.wav and check duration
    soundscape_path = os.path.join(d.get_dscaper_base_path(), "timelines", "timeline4", "generate", generated_data.id, "soundscape.wav")
    data, sr = sf.read(soundscape_path)
    duration = len(data) / sr
    assert abs(duration - 8.0) < 0.1  # duration should be close to 8.0 seconds


def test_generate_timeline_with_event_loops(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=20.0, description="desc", name="timeline5")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add event with event loops
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        event_duration=["const", "10.0"],
        loop_event=True
    )
    resp = d.add_event("timeline5", ev)
    assert resp.status == "success"
    # generate timeline
    gen_props = DscaperGenerate(disable_event_looping=False)
    gen_resp = d.generate_timeline("timeline5", gen_props)
    assert gen_resp.status == "success"
    # TODO: check that event looping worked correctly


def test_generate_timeline_with_relative_event_times(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    # Create a timeline first
    props = DscaperTimeline(duration=15.0, description="desc", name="timeline6")
    resp = d.create_timeline(props)
    assert resp.status == "success"
    # Add audio
    audio_file = os.path.join(os.getcwd(), "tests", "data", "library_inputs", "valid_audio.wav")
    metadata = DscaperAudio(
        library="my_lib",
        label="my_label",
        filename="audio.wav",
    )
    resp = d.store_audio(audio_file, metadata)
    assert resp.status == "success"
    # add event with event time 2.0 seconds after start
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        event_time=["const", "2.0"],  # two seconds after start
    )
    resp = d.add_event("timeline6", ev)
    event_1_id = resp.content["id"]
    assert resp.status == "success"
    # assert end time of event is start time + audio duration
    event_1_data = d._get_event_by_id("timeline6", event_1_id)
    event_1_end = event_1_data.event_end or 0.0
    assert event_1_end - 2.68 < 0.1
    # add event that starts 3.0 seconds after the end of the previous event
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        event_time=["const", "3.0"],  # three seconds after end
        preceding_event=event_1_id  
    )
    resp = d.add_event("timeline6", ev)
    event_2_id = resp.content["id"]
    assert resp.status == "success"
    # assert start and end time of event is correct
    event_2_data = d._get_event_by_id("timeline6", event_2_id)
    event_2_start = event_2_data.event_time
    assert event_2_start[0] == "const"
    assert float(event_2_start[1]) - 3 - event_1_end < 0.1
    event_2_end = event_2_data.event_end or 0.0
    assert event_2_end - 2.8 - 3 - event_1_end < 0.1
    # add event that start directly after the end of the previous event
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        preceding_event=event_2_id
    )
    resp = d.add_event("timeline6", ev)
    event_3_id = resp.content["id"]
    assert resp.status == "success"
    # assert start and end time of event is correct
    event_3_data = d._get_event_by_id("timeline6", event_3_id)
    event_3_start = event_3_data.event_time
    assert event_3_start[0] == "const"
    assert float(event_3_start[1]) - event_2_end < 0.1
    event_3_end = event_3_data.event_end or 0.0
    assert event_3_end - 2.8 - event_2_end < 0.1
    #  add event with incorrect preceding_event ID
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        preceding_event="non-existing-id"  
    )
    resp = d.add_event("timeline6", ev)
    assert resp.status == "error"
    # add event where preceding event has no end time
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        event_duration=["uniform", "1.0", "3.0"],  # random duration
    )
    resp = d.add_event("timeline6", ev)
    event_4_id = resp.content["id"]
    assert resp.status == "success"
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        preceding_event=event_4_id
    )
    resp = d.add_event("timeline6", ev)
    assert resp.status == "error"
    # add event with non constant event time and preceding event
    ev = DscaperEvent(
        library="my_lib",
        label=["const", "my_label"],
        source_file=["const", "audio.wav"],
        event_time=["uniform", "1.0", "5.0"],  # non-constant event time
        preceding_event=event_1_id
    )
    resp = d.add_event("timeline6", ev)
    # assert that event  directly follows the preceding event end
    event_5_id = resp.content["id"]
    event_5_data = d._get_event_by_id("timeline6", event_5_id)
    event_5_start = event_5_data.event_time
    assert event_5_start[0] == "const"
    assert float(event_5_start[1]) - event_1_end < 0.1


def test__get_distribution_tuple(temp_lib_base):
    # const
    d = Dscaper(dscaper_base_path=temp_lib_base)
    assert d._get_distribution_tuple(['const', '7']) == ('const', 7)
    assert d._get_distribution_tuple(['const', 'text']) == ('const', 'text')
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['const', '1', '2'])
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['const', {'invalid': 'format'}])
    # choose
    assert d._get_distribution_tuple(['choose', '[1,2,3]']) == ('choose', ['1', '2', '3'])
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['choose', '[1,2,3]', 'extra'])
    # choose_weighted
    # TODO: check if this is correct
    assert d._get_distribution_tuple(['choose_weighted', '[1,2,3]', '[0.1,0.2,0.7]']) == ('choose_weighted', ['1', '2', '3'], ['0.1', '0.2', '0.7'])
    with pytest.raises(ValueError):
        # TODO: fix this
        # d._get_distribution_tuple(['choose_weighted', '[1,2,3]', '[0.1,0.2]'])
        d._get_distribution_tuple(['choose_weighted', '[1,2,3]'])
    # uniform
    assert d._get_distribution_tuple(['uniform', '1', '10']) == ('uniform', 1, 10)
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['uniform', '1', '10', 'extra'])
    # normal
    assert d._get_distribution_tuple(['normal', '5', '2']) == ('normal', 5, 2)
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['normal', '5', '2', 'extra'])
    # truncnorm
    assert d._get_distribution_tuple(['truncnorm', '5', '2', '1', '10']) == ('truncnorm', 5, 2, 1, 10)
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['truncnorm', '5', '2', '1', '10', 'extra'])
    # invalidnormal
    with pytest.raises(ValueError):
        d._get_distribution_tuple(['invalidnormal', '5', '2'])
    # invalid format
    with pytest.raises(ValueError):
        d._get_distribution_tuple({'invalid_format'})


def test__string_to_list(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    assert d._string_to_list("[a, b, c]") == ["a", "b", "c"]
    assert d._string_to_list("[]") == []
    assert d._string_to_list("a, b") == ["a", "b"]
    assert d._string_to_list("a") == ["a"]
    assert d._string_to_list("") == []
    with pytest.raises(ValueError):
        d._string_to_list(['a', 'b', 'c'])
    # Test with quotes
    # assert d._string_to_list('["a", "b", "c"]') == ["a", "b", "c"]
    # assert d._string_to_list('"a"') == ["a"]


def test__isfloat(temp_lib_base):
    d = Dscaper(dscaper_base_path=temp_lib_base)
    assert d._isfloat("3.14") is True
    assert d._isfloat("0.001") is True
    assert d._isfloat("-2.5") is True
    assert d._isfloat("abc") is False
    assert d._isfloat("123") is True  # Integers are not considered floats in this context
    assert d._isfloat("") is False
    assert d._isfloat(None) is False
