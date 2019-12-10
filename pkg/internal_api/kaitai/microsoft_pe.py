# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from ...vendor.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class MicrosoftPe(KaitaiStruct):
    """
    .. seealso::
       Source - http://www.microsoft.com/whdc/system/platform/firmware/PECOFF.mspx
    """

    class PeFormat(Enum):
        rom_image = 263
        pe32 = 267
        pe32_plus = 523
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.mz = self._root.MzPlaceholder(self._io, self, self._root)

    class CertificateEntry(KaitaiStruct):
        """
        .. seealso::
           Source - https://docs.microsoft.com/en-us/windows/desktop/debug/pe-format#the-attribute-certificate-table-image-only
        """

        class CertificateRevision(Enum):
            revision_1_0 = 256
            revision_2_0 = 512

        class CertificateType(Enum):
            x509 = 1
            pkcs_signed_data = 2
            reserved_1 = 3
            ts_stack_signed = 4
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.length = self._io.read_u4le()
            self.revision = self._root.CertificateEntry.CertificateRevision(self._io.read_u2le())
            self.certificate_type = self._root.CertificateEntry.CertificateType(self._io.read_u2le())
            self.certificate_bytes = self._io.read_bytes((self.length - 8))


    class OptionalHeaderWindows(KaitaiStruct):

        class SubsystemEnum(Enum):
            unknown = 0
            native = 1
            windows_gui = 2
            windows_cui = 3
            posix_cui = 7
            windows_ce_gui = 9
            efi_application = 10
            efi_boot_service_driver = 11
            efi_runtime_driver = 12
            efi_rom = 13
            xbox = 14
            windows_boot_application = 16
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            if self._parent.std.format == self._root.PeFormat.pe32:
                self.image_base_32 = self._io.read_u4le()

            if self._parent.std.format == self._root.PeFormat.pe32_plus:
                self.image_base_64 = self._io.read_u8le()

            self.section_alignment = self._io.read_u4le()
            self.file_alignment = self._io.read_u4le()
            self.major_operating_system_version = self._io.read_u2le()
            self.minor_operating_system_version = self._io.read_u2le()
            self.major_image_version = self._io.read_u2le()
            self.minor_image_version = self._io.read_u2le()
            self.major_subsystem_version = self._io.read_u2le()
            self.minor_subsystem_version = self._io.read_u2le()
            self.win32_version_value = self._io.read_u4le()
            self.size_of_image = self._io.read_u4le()
            self.size_of_headers = self._io.read_u4le()
            self.check_sum = self._io.read_u4le()
            self.subsystem = self._root.OptionalHeaderWindows.SubsystemEnum(self._io.read_u2le())
            self.dll_characteristics = self._io.read_u2le()
            if self._parent.std.format == self._root.PeFormat.pe32:
                self.size_of_stack_reserve_32 = self._io.read_u4le()

            if self._parent.std.format == self._root.PeFormat.pe32_plus:
                self.size_of_stack_reserve_64 = self._io.read_u8le()

            if self._parent.std.format == self._root.PeFormat.pe32:
                self.size_of_stack_commit_32 = self._io.read_u4le()

            if self._parent.std.format == self._root.PeFormat.pe32_plus:
                self.size_of_stack_commit_64 = self._io.read_u8le()

            if self._parent.std.format == self._root.PeFormat.pe32:
                self.size_of_heap_reserve_32 = self._io.read_u4le()

            if self._parent.std.format == self._root.PeFormat.pe32_plus:
                self.size_of_heap_reserve_64 = self._io.read_u8le()

            if self._parent.std.format == self._root.PeFormat.pe32:
                self.size_of_heap_commit_32 = self._io.read_u4le()

            if self._parent.std.format == self._root.PeFormat.pe32_plus:
                self.size_of_heap_commit_64 = self._io.read_u8le()

            self.loader_flags = self._io.read_u4le()
            self.number_of_rva_and_sizes = self._io.read_u4le()


    class OptionalHeaderDataDirs(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.export_table = self._root.DataDir(self._io, self, self._root)
            self.import_table = self._root.DataDir(self._io, self, self._root)
            self.resource_table = self._root.DataDir(self._io, self, self._root)
            self.exception_table = self._root.DataDir(self._io, self, self._root)
            self.certificate_table = self._root.DataDir(self._io, self, self._root)
            self.base_relocation_table = self._root.DataDir(self._io, self, self._root)
            self.debug = self._root.DataDir(self._io, self, self._root)
            self.architecture = self._root.DataDir(self._io, self, self._root)
            self.global_ptr = self._root.DataDir(self._io, self, self._root)
            self.tls_table = self._root.DataDir(self._io, self, self._root)
            self.load_config_table = self._root.DataDir(self._io, self, self._root)
            self.bound_import = self._root.DataDir(self._io, self, self._root)
            self.iat = self._root.DataDir(self._io, self, self._root)
            self.delay_import_descriptor = self._root.DataDir(self._io, self, self._root)
            self.clr_runtime_header = self._root.DataDir(self._io, self, self._root)


    class DataDir(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.virtual_address = self._io.read_u4le()
            self.size = self._io.read_u4le()


    class CoffSymbol(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._raw_name_annoying = self._io.read_bytes(8)
            io = KaitaiStream(BytesIO(self._raw_name_annoying))
            self.name_annoying = self._root.Annoyingstring(io, self, self._root)
            self.value = self._io.read_u4le()
            self.section_number = self._io.read_u2le()
            self.type = self._io.read_u2le()
            self.storage_class = self._io.read_u1()
            self.number_of_aux_symbols = self._io.read_u1()

        @property
        def section(self):
            if hasattr(self, '_m_section'):
                return self._m_section if hasattr(self, '_m_section') else None

            self._m_section = self._root.pe.sections[(self.section_number - 1)]
            return self._m_section if hasattr(self, '_m_section') else None

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data if hasattr(self, '_m_data') else None

            _pos = self._io.pos()
            self._io.seek((self.section.pointer_to_raw_data + self.value))
            self._m_data = self._io.read_bytes(1)
            self._io.seek(_pos)
            return self._m_data if hasattr(self, '_m_data') else None


    class PeHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.pe_signature = self._io.ensure_fixed_contents(b"\x50\x45\x00\x00")
            self.coff_hdr = self._root.CoffHeader(self._io, self, self._root)
            self._raw_optional_hdr = self._io.read_bytes(self.coff_hdr.size_of_optional_header)
            io = KaitaiStream(BytesIO(self._raw_optional_hdr))
            self.optional_hdr = self._root.OptionalHeader(io, self, self._root)
            self.sections = [None] * (self.coff_hdr.number_of_sections)
            for i in range(self.coff_hdr.number_of_sections):
                self.sections[i] = self._root.Section(self._io, self, self._root)


        @property
        def certificate_table(self):
            if hasattr(self, '_m_certificate_table'):
                return self._m_certificate_table if hasattr(self, '_m_certificate_table') else None

            if self.optional_hdr.data_dirs.certificate_table.virtual_address != 0:
                _pos = self._io.pos()
                self._io.seek(self.optional_hdr.data_dirs.certificate_table.virtual_address)
                self._raw__m_certificate_table = self._io.read_bytes(self.optional_hdr.data_dirs.certificate_table.size)
                io = KaitaiStream(BytesIO(self._raw__m_certificate_table))
                self._m_certificate_table = self._root.CertificateTable(io, self, self._root)
                self._io.seek(_pos)

            return self._m_certificate_table if hasattr(self, '_m_certificate_table') else None


    class OptionalHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.std = self._root.OptionalHeaderStd(self._io, self, self._root)
            self.windows = self._root.OptionalHeaderWindows(self._io, self, self._root)
            self.data_dirs = self._root.OptionalHeaderDataDirs(self._io, self, self._root)


    class Section(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.name = (KaitaiStream.bytes_strip_right(self._io.read_bytes(8), 0)).decode(u"UTF-8")
            self.virtual_size = self._io.read_u4le()
            self.virtual_address = self._io.read_u4le()
            self.size_of_raw_data = self._io.read_u4le()
            self.pointer_to_raw_data = self._io.read_u4le()
            self.pointer_to_relocations = self._io.read_u4le()
            self.pointer_to_linenumbers = self._io.read_u4le()
            self.number_of_relocations = self._io.read_u2le()
            self.number_of_linenumbers = self._io.read_u2le()
            self.characteristics = self._io.read_u4le()

        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body if hasattr(self, '_m_body') else None

            _pos = self._io.pos()
            self._io.seek(self.pointer_to_raw_data)
            self._m_body = self._io.read_bytes(self.size_of_raw_data)
            self._io.seek(_pos)
            return self._m_body if hasattr(self, '_m_body') else None


    class CertificateTable(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.items = []
            i = 0
            while not self._io.is_eof():
                self.items.append(self._root.CertificateEntry(self._io, self, self._root))
                i += 1



    class MzPlaceholder(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.ensure_fixed_contents(b"\x4D\x5A")
            self.data1 = self._io.read_bytes(58)
            self.ofs_pe = self._io.read_u4le()


    class OptionalHeaderStd(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.format = self._root.PeFormat(self._io.read_u2le())
            self.major_linker_version = self._io.read_u1()
            self.minor_linker_version = self._io.read_u1()
            self.size_of_code = self._io.read_u4le()
            self.size_of_initialized_data = self._io.read_u4le()
            self.size_of_uninitialized_data = self._io.read_u4le()
            self.address_of_entry_point = self._io.read_u4le()
            self.base_of_code = self._io.read_u4le()
            if self.format == self._root.PeFormat.pe32:
                self.base_of_data = self._io.read_u4le()



    class CoffHeader(KaitaiStruct):
        """
        .. seealso::
           3.3. COFF File Header (Object and Image)
        """

        class MachineType(Enum):
            unknown = 0
            i386 = 332
            r4000 = 358
            wcemipsv2 = 361
            alpha = 388
            sh3 = 418
            sh3dsp = 419
            sh4 = 422
            sh5 = 424
            arm = 448
            thumb = 450
            armnt = 452
            am33 = 467
            powerpc = 496
            powerpcfp = 497
            ia64 = 512
            mips16 = 614
            mipsfpu = 870
            mipsfpu16 = 1126
            ebc = 3772
            riscv32 = 20530
            riscv64 = 20580
            riscv128 = 20776
            amd64 = 34404
            m32r = 36929
            arm64 = 43620
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.machine = self._root.CoffHeader.MachineType(self._io.read_u2le())
            self.number_of_sections = self._io.read_u2le()
            self.time_date_stamp = self._io.read_u4le()
            self.pointer_to_symbol_table = self._io.read_u4le()
            self.number_of_symbols = self._io.read_u4le()
            self.size_of_optional_header = self._io.read_u2le()
            self.characteristics = self._io.read_u2le()

        @property
        def symbol_table_size(self):
            if hasattr(self, '_m_symbol_table_size'):
                return self._m_symbol_table_size if hasattr(self, '_m_symbol_table_size') else None

            self._m_symbol_table_size = (self.number_of_symbols * 18)
            return self._m_symbol_table_size if hasattr(self, '_m_symbol_table_size') else None

        @property
        def symbol_name_table_offset(self):
            if hasattr(self, '_m_symbol_name_table_offset'):
                return self._m_symbol_name_table_offset if hasattr(self, '_m_symbol_name_table_offset') else None

            self._m_symbol_name_table_offset = (self.pointer_to_symbol_table + self.symbol_table_size)
            return self._m_symbol_name_table_offset if hasattr(self, '_m_symbol_name_table_offset') else None

        @property
        def symbol_name_table_size(self):
            if hasattr(self, '_m_symbol_name_table_size'):
                return self._m_symbol_name_table_size if hasattr(self, '_m_symbol_name_table_size') else None

            _pos = self._io.pos()
            self._io.seek(self.symbol_name_table_offset)
            self._m_symbol_name_table_size = self._io.read_u4le()
            self._io.seek(_pos)
            return self._m_symbol_name_table_size if hasattr(self, '_m_symbol_name_table_size') else None

        @property
        def symbol_table(self):
            if hasattr(self, '_m_symbol_table'):
                return self._m_symbol_table if hasattr(self, '_m_symbol_table') else None

            _pos = self._io.pos()
            self._io.seek(self.pointer_to_symbol_table)
            self._m_symbol_table = [None] * (self.number_of_symbols)
            for i in range(self.number_of_symbols):
                self._m_symbol_table[i] = self._root.CoffSymbol(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_symbol_table if hasattr(self, '_m_symbol_table') else None


    class Annoyingstring(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def name_from_offset(self):
            if hasattr(self, '_m_name_from_offset'):
                return self._m_name_from_offset if hasattr(self, '_m_name_from_offset') else None

            if self.name_zeroes == 0:
                io = self._root._io
                _pos = io.pos()
                io.seek(((self._parent._parent.symbol_name_table_offset + self.name_offset) if self.name_zeroes == 0 else 0))
                self._m_name_from_offset = (io.read_bytes_term(0, False, True, False)).decode(u"ascii")
                io.seek(_pos)

            return self._m_name_from_offset if hasattr(self, '_m_name_from_offset') else None

        @property
        def name_offset(self):
            if hasattr(self, '_m_name_offset'):
                return self._m_name_offset if hasattr(self, '_m_name_offset') else None

            _pos = self._io.pos()
            self._io.seek(4)
            self._m_name_offset = self._io.read_u4le()
            self._io.seek(_pos)
            return self._m_name_offset if hasattr(self, '_m_name_offset') else None

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name if hasattr(self, '_m_name') else None

            self._m_name = (self.name_from_offset if self.name_zeroes == 0 else self.name_from_short)
            return self._m_name if hasattr(self, '_m_name') else None

        @property
        def name_zeroes(self):
            if hasattr(self, '_m_name_zeroes'):
                return self._m_name_zeroes if hasattr(self, '_m_name_zeroes') else None

            _pos = self._io.pos()
            self._io.seek(0)
            self._m_name_zeroes = self._io.read_u4le()
            self._io.seek(_pos)
            return self._m_name_zeroes if hasattr(self, '_m_name_zeroes') else None

        @property
        def name_from_short(self):
            if hasattr(self, '_m_name_from_short'):
                return self._m_name_from_short if hasattr(self, '_m_name_from_short') else None

            if self.name_zeroes != 0:
                _pos = self._io.pos()
                self._io.seek(0)
                self._m_name_from_short = (self._io.read_bytes_term(0, False, True, False)).decode(u"ascii")
                self._io.seek(_pos)

            return self._m_name_from_short if hasattr(self, '_m_name_from_short') else None


    @property
    def pe(self):
        if hasattr(self, '_m_pe'):
            return self._m_pe if hasattr(self, '_m_pe') else None

        _pos = self._io.pos()
        self._io.seek(self.mz.ofs_pe)
        self._m_pe = self._root.PeHeader(self._io, self, self._root)
        self._io.seek(_pos)
        return self._m_pe if hasattr(self, '_m_pe') else None


