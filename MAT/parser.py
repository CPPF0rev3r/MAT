'''
    Parent class of all parser
'''

import hachoir_core
import hachoir_editor

import os

import mat

NOMETA = ('.bmp',  # image
          '.rdf',  # text
          '.txt',  # plain text
          '.xml',  # formated text (XML)
          '.rels', # openXML formated text
          )

FIELD = object()


class GenericParser(object):
    '''
        Parent class of all parsers
    '''
    def __init__(self, filename, parser, mime, backup, **kwargs):
        self.filename = ''
        self.parser = parser
        self.mime = mime
        self.backup = backup
        self.editor = hachoir_editor.createEditor(parser)
        self.realname = filename
        try:
            self.filename = hachoir_core.cmd_line.unicodeFilename(filename)
        except TypeError:  # get rid of "decoding Unicode is not supported"
            self.filename = filename
        basename, ext = os.path.splitext(filename)
        self.output = basename + '.cleaned' + ext
        self.basename = os.path.basename(filename)  # only filename

    def is_clean(self):
        '''
            Check if the file is clean from harmful metadatas
        '''
        for field in self.editor:
            if self._should_remove(field):
                return self._is_clean(self.editor)
        return True

    def _is_clean(self, fieldset):
        for field in fieldset:
            remove = self._should_remove(field)
            if remove is True:
                return False
            if remove is FIELD:
                if not self._is_clean(field):
                    return False
        return True

    def remove_all(self):
        '''
            Remove all compromising fields
        '''
        state = self._remove_all(self.editor)
        hachoir_core.field.writeIntoFile(self.editor, self.output)
        self.do_backup()
        return state

    def _remove_all(self, fieldset):
        '''
            Recursive way to handle tree metadatas
        '''
        try:
            for field in fieldset:
                remove = self._should_remove(field)
                if remove is True:
                    self._remove(fieldset, field.name)
                if remove is FIELD:
                    self._remove_all(field)
            return True
        except:
            return False

    def _remove(self, fieldset, field):
        '''
            Delete the given field
        '''
        del fieldset[field]

    def get_meta(self):
        '''
            Return a dict with all the meta of the file
        '''
        metadata = {}
        self._get_meta(self.editor, metadata)
        return metadata

    def _get_meta(self, fieldset, metadata):
        '''
            Recursive way to handle tree metadatas
        '''
        for field in fieldset:
            remove = self._should_remove(field)
            if remove is True:
                try:
                    metadata[field.name] = field.value
                except:
                    metadata[field.name] = 'harmful content'
            if remove is FIELD:
                self._get_meta(field, None)

    def _should_remove(self, key):
        '''
            return True if the field is compromising
            abstract method
        '''
        raise NotImplementedError

    def do_backup(self):
        '''
            Do a backup of the file if asked,
            and change his creation/access date
        '''
        if not self.backup:
            mat.secure_remove(self.filename)
            os.rename(self.output, self.filename)