"""
Módulo de Validación de CURP
============================
Valida CURPs contra base de datos y algoritmo de validación
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CURPValidator:
    """Validador de CURP con verificación de base de datos"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Catálogos oficiales
        self.estados = {
            'AS': 'AGUASCALIENTES', 'BC': 'BAJA CALIFORNIA', 'BS': 'BAJA CALIFORNIA SUR',
            'CC': 'CAMPECHE', 'CL': 'COAHUILA', 'CM': 'COLIMA', 'CS': 'CHIAPAS',
            'CH': 'CHIHUAHUA', 'DF': 'CIUDAD DE MEXICO', 'DG': 'DURANGO',
            'GT': 'GUANAJUATO', 'GR': 'GUERRERO', 'HG': 'HIDALGO', 'JC': 'JALISCO',
            'MC': 'MEXICO', 'MN': 'MICHOACAN', 'MS': 'MORELOS', 'NT': 'NAYARIT',
            'NL': 'NUEVO LEON', 'OC': 'OAXACA', 'PL': 'PUEBLA', 'QT': 'QUERETARO',
            'QR': 'QUINTANA ROO', 'SP': 'SAN LUIS POTOSI', 'SL': 'SINALOA',
            'SR': 'SONORA', 'TC': 'TABASCO', 'TS': 'TAMAULIPAS', 'TL': 'TLAXCALA',
            'VZ': 'VERACRUZ', 'YN': 'YUCATAN', 'ZS': 'ZACATECAS', 'NE': 'NACIDO EXTRANJERO'
        }
        
        # Palabras inconvenientes que se reemplazan
        self.palabras_inconvenientes = [
            'BUEI', 'BUEY', 'CACA', 'CACO', 'CAGA', 'CAGO', 'CAKA', 'CAKO',
            'COGE', 'COGI', 'COJA', 'COJE', 'COJI', 'COJO', 'COLA', 'CULO',
            'FALO', 'FETO', 'GETA', 'GUEI', 'GUEY', 'JETA', 'JOTO', 'KACA',
            'KACO', 'KAGA', 'KAGO', 'KAKA', 'KAKO', 'KOGE', 'KOGI', 'KOJA',
            'KOJE', 'KOJI', 'KOJO', 'KOLA', 'KULO', 'LILO', 'LOCA', 'LOCO',
            'LOKA', 'LOKO', 'MAME', 'MAMO', 'MEAR', 'MEAS', 'MEON', 'MIAR',
            'MION', 'MOCO', 'MOKO', 'MULA', 'MULO', 'NACA', 'NACO', 'PEDA',
            'PEDO', 'PENE', 'PIPI', 'PITO', 'POPO', 'PUTA', 'PUTO', 'QULO',
            'RATA', 'ROBA', 'ROBE', 'ROBO', 'RUIN', 'SENO', 'TETA', 'VACA',
            'VAGA', 'VAGO', 'VAKA', 'VUEI', 'VUEY', 'WUEI', 'WUEY'
        ]
    
    def validate_format(self, curp: str) -> Dict[str, Any]:
        """Valida el formato de la CURP"""
        
        # Normalizar
        curp = curp.upper().strip()
        
        # Validar longitud
        if len(curp) != 18:
            return {
                "is_valid": False,
                "message": f"CURP debe tener 18 caracteres (tiene {len(curp)})"
            }
        
        # Validar patrón general
        pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$'
        if not re.match(pattern, curp):
            return {
                "is_valid": False,
                "message": "Formato de CURP inválido"
            }
        
        # Extraer componentes
        apellido_paterno = curp[0]
        primera_vocal = curp[1]
        apellido_materno = curp[2]
        nombre = curp[3]
        fecha_nac = curp[4:10]  # YYMMDD
        sexo = curp[10]
        estado = curp[11:13]
        consonantes = curp[13:16]
        homoclave = curp[16]
        digito_verificador = curp[17]
        
        # Validar fecha
        try:
            year = int(fecha_nac[0:2])
            # Determinar siglo (00-29 = 2000s, 30-99 = 1900s)
            year_full = 2000 + year if year <= 29 else 1900 + year
            month = int(fecha_nac[2:4])
            day = int(fecha_nac[4:6])
            
            birth_date = datetime(year_full, month, day)
            
            # Validar que no sea futuro
            if birth_date > datetime.now():
                return {
                    "is_valid": False,
                    "message": "Fecha de nacimiento no puede ser futura"
                }
            
            # Validar edad razonable (< 150 años)
            age = (datetime.now() - birth_date).days / 365.25
            if age > 150:
                return {
                    "is_valid": False,
                    "message": "Fecha de nacimiento no válida (edad > 150 años)"
                }
                
        except ValueError:
            return {
                "is_valid": False,
                "message": "Fecha de nacimiento inválida en CURP"
            }
        
        # Validar sexo
        if sexo not in ['H', 'M']:
            return {
                "is_valid": False,
                "message": f"Sexo debe ser H o M (encontrado: {sexo})"
            }
        
        # Validar estado
        if estado not in self.estados:
            return {
                "is_valid": False,
                "message": f"Estado inválido: {estado}"
            }
        
        # Validar dígito verificador
        if not self._validate_check_digit(curp):
            return {
                "is_valid": False,
                "message": "Dígito verificador incorrecto"
            }
        
        # Detectar palabras inconvenientes
        primeros_4 = curp[0:4]
        if primeros_4 in self.palabras_inconvenientes:
            logger.warning(f"CURP contiene palabra inconveniente: {primeros_4}")
        
        return {
            "is_valid": True,
            "message": "Formato de CURP válido",
            "components": {
                "birth_date": birth_date.strftime("%Y-%m-%d"),
                "sex": "Hombre" if sexo == "H" else "Mujer",
                "state": self.estados[estado],
                "state_code": estado
            }
        }
    
    def _validate_check_digit(self, curp: str) -> bool:
        """Valida el dígito verificador de la CURP"""
        
        # Diccionario de valores para el cálculo
        values = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
        
        suma = 0
        for i, char in enumerate(curp[:17]):
            suma += values.index(char) * (18 - i)
        
        digito_calculado = 10 - (suma % 10)
        if digito_calculado == 10:
            digito_calculado = 0
        
        digito_curp = int(curp[17]) if curp[17].isdigit() else values.index(curp[17])
        
        return digito_calculado == digito_curp
    
    async def validate(
        self,
        curp: str,
        full_name: Optional[str] = None,
        birth_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida CURP completo (formato + base de datos)
        
        Args:
            curp: CURP a validar
            full_name: Nombre completo para verificar coincidencia
            birth_date: Fecha de nacimiento DD/MM/YYYY para verificar
        
        Returns:
            Dict con resultado de validación
        """
        
        # 1. Validar formato
        format_validation = self.validate_format(curp)
        
        if not format_validation["is_valid"]:
            return {
                **format_validation,
                "source": "format_validation",
                "database_check": False
            }
        
        # 2. Verificar en base de datos (si está disponible)
        try:
            db_result = await self.db.check_curp(curp)
            
            result = {
                **format_validation,
                "database_check": True,
                "exists_in_db": db_result["exists"],
                "source": "database"
            }
            
            if db_result["exists"]:
                db_data = db_result["data"]
                result["registered_name"] = db_data.get("nombre_completo")
                result["registered_birth_date"] = db_data.get("fecha_nacimiento")
                
                # Verificar coincidencia de nombre si se proporcionó
                if full_name and db_data.get("nombre_completo"):
                    name_match = self._compare_names(
                        full_name,
                        db_data["nombre_completo"]
                    )
                    result["name_match"] = name_match
                    
                    if not name_match:
                        result["is_valid"] = False
                        result["message"] = "CURP válido pero nombre no coincide con registro"
                
                # Verificar coincidencia de fecha si se proporcionó
                if birth_date:
                    date_match = self._compare_dates(
                        birth_date,
                        format_validation["components"]["birth_date"]
                    )
                    result["birth_date_match"] = date_match
                    
                    if not date_match:
                        result["is_valid"] = False
                        result["message"] = "CURP válido pero fecha de nacimiento no coincide"
            
            else:
                result["is_valid"] = False
                result["message"] = "CURP con formato válido pero no encontrado en base de datos oficial"
            
            return result
            
        except Exception as e:
            logger.error(f"Error verificando CURP en BD: {e}")
            
            # Si falla la BD, retornar solo validación de formato
            return {
                **format_validation,
                "database_check": False,
                "error": f"No se pudo verificar en base de datos: {str(e)}",
                "warning": "Solo se validó el formato, no la existencia en RENAPO"
            }
    
    def _compare_names(self, name1: str, name2: str) -> bool:
        """Compara dos nombres considerando variaciones comunes"""
        
        def normalize_name(name: str) -> str:
            """Normaliza nombre para comparación"""
            name = name.upper().strip()
            # Remover acentos
            replacements = {
                'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'Ü': 'U', 'Ñ': 'N'
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            # Remover múltiples espacios
            name = ' '.join(name.split())
            return name
        
        norm1 = normalize_name(name1)
        norm2 = normalize_name(name2)
        
        # Coincidencia exacta
        if norm1 == norm2:
            return True
        
        # Coincidencia parcial (al menos 80% de las palabras coinciden)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        similarity = len(intersection) / max(len(words1), len(words2))
        
        return similarity >= 0.8
    
    def _compare_dates(self, date1: str, date2: str) -> bool:
        """Compara dos fechas (soporta DD/MM/YYYY y YYYY-MM-DD)"""
        
        def parse_date(date_str: str) -> datetime:
            """Parsea fecha en múltiples formatos"""
            formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha no reconocido: {date_str}")
        
        try:
            d1 = parse_date(date1)
            d2 = parse_date(date2)
            return d1.date() == d2.date()
        except ValueError as e:
            logger.warning(f"Error comparando fechas: {e}")
            return False
    
    def generate_curp(
        self,
        first_name: str,
        paternal_surname: str,
        maternal_surname: str,
        birth_date: str,  # DD/MM/YYYY
        sex: str,  # H o M
        state_code: str
    ) -> str:
        """
        Genera una CURP a partir de datos personales
        (Solo para referencia, la CURP oficial debe obtenerse de RENAPO)
        """
        
        def get_first_vowel(word: str) -> str:
            """Obtiene la primera vocal interna de una palabra"""
            vowels = "AEIOU"
            word = word.upper()
            for i, char in enumerate(word[1:], 1):
                if char in vowels:
                    return char
            return "X"
        
        def get_first_consonant(word: str) -> str:
            """Obtiene la primera consonante interna"""
            consonants = "BCDFGHJKLMNÑPQRSTVWXYZ"
            word = word.upper()
            for i, char in enumerate(word[1:], 1):
                if char in consonants:
                    return char
            return "X"
        
        # Normalizar entradas
        first_name = first_name.upper().strip()
        paternal_surname = paternal_surname.upper().strip()
        maternal_surname = maternal_surname.upper().strip()
        
        # Manejar nombres compuestos (usar solo el primero)
        if ' ' in first_name:
            # Ignorar nombres comunes que no cuentan
            ignore_names = ['MARIA', 'JOSE', 'MA', 'MA.', 'J', 'J.']
            parts = first_name.split()
            first_name = next((p for p in parts if p not in ignore_names), parts[0])
        
        # Construir primeros 4 caracteres
        letra1 = paternal_surname[0]
        vocal1 = get_first_vowel(paternal_surname)
        letra2 = maternal_surname[0] if maternal_surname else "X"
        letra3 = first_name[0]
        
        primeros_4 = f"{letra1}{vocal1}{letra2}{letra3}"
        
        # Reemplazar si es palabra inconveniente
        if primeros_4 in self.palabras_inconvenientes:
            primeros_4 = primeros_4[:3] + "X"
        
        # Fecha de nacimiento (YYMMDD)
        date_obj = datetime.strptime(birth_date, "%d/%m/%Y")
        fecha = date_obj.strftime("%y%m%d")
        
        # Sexo
        sexo = sex.upper()
        
        # Estado
        estado = state_code.upper()
        
        # Consonantes internas
        cons1 = get_first_consonant(paternal_surname)
        cons2 = get_first_consonant(maternal_surname) if maternal_surname else "X"
        cons3 = get_first_consonant(first_name)
        
        # Homoclave (simplificada - la real requiere tabla compleja)
        # En producción esto debe obtenerse de RENAPO
        homoclave = "0"
        
        # Construir CURP sin dígito verificador
        curp_sin_digito = f"{primeros_4}{fecha}{sexo}{estado}{cons1}{cons2}{cons3}{homoclave}"
        
        # Calcular dígito verificador
        values = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
        suma = 0
        for i, char in enumerate(curp_sin_digito):
            suma += values.index(char) * (18 - i)
        
        digito = 10 - (suma % 10)
        if digito == 10:
            digito = 0
        
        curp_final = f"{curp_sin_digito}{digito}"
        
        return curp_final
