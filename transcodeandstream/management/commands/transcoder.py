from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import time
import os
import sys

from transcodeandstream.models import EncodeQueueEntry
from transcodeandstream.settings import TAS_TRANSCODER_POLL_SECONDS, TAS_VIDEOS_DIRECTORY, TAS_FFMPEG_EXECUTABLE, TAS_FFMPEG_OPTIONS

from _transcoder import encode


def progress_callback(id, progress, log):
    entry = EncodeQueueEntry.objects.get(pk=id)
    entry.progress = progress
    if log:
        entry.log = '\n'.join([entry.log, log]) if entry.log else log
    entry.save()


def finish_callback(id, status):
    entry = EncodeQueueEntry.objects.get(pk=id)
    # TODO: add record to video management
    if status == 0:
        entry.delete()
    else:
        entry.error = True
        entry.save()


class Command(BaseCommand):
    help = 'Encode videos'

    def handle(self, *args, **options):
        while True:
            try:
                entry = EncodeQueueEntry.objects.get_new_entries()[0]
                entry.working_on = True
                entry.save()
                encode(
                    entry.pk,
                    entry.original_filename,
                    TAS_VIDEOS_DIRECTORY,
                    TAS_FFMPEG_EXECUTABLE,
                    TAS_FFMPEG_OPTIONS,
                    progress_callback,
                    finish_callback,
                )
            except IndexError:
                pass
            time.sleep(TAS_TRANSCODER_POLL_SECONDS)