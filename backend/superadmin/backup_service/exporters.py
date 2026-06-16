"""Exportação CSV e compactação ZIP para backup."""
import csv
import io
import logging
import zipfile
from datetime import datetime
from decimal import Decimal
from typing import List

from django.utils import timezone

logger = logging.getLogger(__name__)

class CSVExporter:
    """
    Exportador de dados para CSV.
    
    Responsável por converter dados do banco em arquivos CSV.
    """
    
    @staticmethod
    def export_table_to_csv(
        table_name: str,
        columns: List[str],
        records: List[tuple]
    ) -> bytes:
        """
        Exporta uma tabela para CSV em memória.
        
        Args:
            table_name: Nome da tabela
            columns: Lista de colunas
            records: Lista de registros
        
        Returns:
            bytes: Conteúdo do CSV em bytes
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Escrever cabeçalho
        writer.writerow(columns)
        
        # Escrever registros
        for record in records:
            # Converter valores para string, tratando None e tipos especiais
            row = [CSVExporter._format_value(val) for val in record]
            writer.writerow(row)
        
        # Converter para bytes
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')
    
    @staticmethod
    def _format_value(value):
        """Formata um valor para CSV"""
        if value is None:
            return ''
        if isinstance(value, (datetime, timezone.datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, bool):
            return '1' if value else '0'
        return str(value)


class ZipBuilder:
    """
    Construtor de arquivos ZIP.
    
    Responsável por criar o arquivo ZIP com todos os CSVs.
    """
    
    def __init__(self):
        self.zip_buffer = io.BytesIO()
        self.zip_file = zipfile.ZipFile(
            self.zip_buffer,
            'w',
            zipfile.ZIP_DEFLATED,
            compresslevel=9
        )
    
    def add_csv(self, filename: str, csv_content: bytes):
        """Adiciona um arquivo CSV ao ZIP"""
        self.zip_file.writestr(filename, csv_content)

    def add_file(self, filename: str, content: bytes):
        """Adiciona arquivo binário ao ZIP (imagens, PDFs, etc.)."""
        self.zip_file.writestr(filename, content)
    
    def add_metadata(self, metadata: dict):
        """Adiciona arquivo de metadados ao ZIP"""
        import json
        metadata_json = json.dumps(metadata, indent=2, default=str)
        self.zip_file.writestr('_metadata.json', metadata_json)
    
    def finalize(self) -> bytes:
        """Finaliza o ZIP e retorna os bytes"""
        self.zip_file.close()
        zip_bytes = self.zip_buffer.getvalue()
        self.zip_buffer.close()
        return zip_bytes
    
    def get_size_mb(self, zip_bytes: bytes) -> float:
        """Calcula tamanho em MB"""
        return len(zip_bytes) / (1024 * 1024)
