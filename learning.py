import sqlite3
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class LearningSystem:
    def __init__(self, db_path: str = "learning_patterns.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Tabela de regras aprendidas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_text TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    success_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL DEFAULT 0.5
                )
            """)
            
            # Tabela de padrões de transformação
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transformation_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    success_rate REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de sugestões pendentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    suggested_text TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    pattern_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (pattern_id) REFERENCES learned_rules(id)
                )
            """)
            
            # Tabela de rejeições (padrões que foram rejeitados)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rejected_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    suggested_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(original_text, suggested_text)
                )
            """)
            
            conn.commit()
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação"""
        text = text.lower().strip()
        return re.sub(r"\s+", " ", text)
    
    def analyze_transformation(self, original: str, transformed: str) -> Dict:
        """Analisa uma transformação e extrai padrões"""
        original_norm = self.normalize_text(original)
        transformed_norm = self.normalize_text(transformed)
        
        patterns = {
            'removed_words': [],
            'added_words': [],
            'word_replacements': [],
            'case_changes': original != transformed and original.lower() == transformed.lower(),
            'similarity': SequenceMatcher(None, original_norm, transformed_norm).ratio()
        }
        
        # Identifica palavras removidas
        original_words = set(original_norm.split())
        transformed_words = set(transformed_norm.split())
        patterns['removed_words'] = list(original_words - transformed_words)
        patterns['added_words'] = list(transformed_words - original_words)
        
        # Identifica substituições de palavras similares
        for orig_word in original_words:
            for trans_word in transformed_words:
                similarity = SequenceMatcher(None, orig_word, trans_word).ratio()
                if similarity > 0.7 and orig_word != trans_word:
                    patterns['word_replacements'].append({
                        'from': orig_word,
                        'to': trans_word,
                        'similarity': similarity
                    })
        
        return patterns
    
    def learn_rule(self, pattern_text: str, target_text: str):
        """Aprende uma nova regra manual"""
        if not pattern_text or not target_text:
            return None
            
        pattern_norm = self.normalize_text(pattern_text)
        target_norm = self.normalize_text(target_text)
        
        if not pattern_norm or not target_norm:
            return None
        
        # Usa context manager para garantir fechamento da conexão
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Verifica se a regra já existe
            cursor.execute("""
                SELECT id, usage_count, success_count FROM learned_rules
                WHERE pattern_text = ? AND target_text = ?
            """, (pattern_norm, target_norm))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualiza regra existente
                rule_id, usage_count, success_count = existing
                cursor.execute("""
                    UPDATE learned_rules
                    SET usage_count = usage_count + 1,
                        last_used = CURRENT_TIMESTAMP,
                        confidence = CAST(success_count AS REAL) / usage_count
                    WHERE id = ?
                """, (rule_id,))
            else:
                # Cria nova regra
                cursor.execute("""
                    INSERT INTO learned_rules (pattern_text, target_text, usage_count, success_count, confidence)
                    VALUES (?, ?, 1, 0, 0.5)
                """, (pattern_norm, target_norm))
                rule_id = cursor.lastrowid
            
            # Analisa e armazena padrões de transformação
            try:
                transformation = self.analyze_transformation(pattern_text, target_text)
                
                # Armazena padrões de remoção de palavras
                for word in transformation.get('removed_words', []):
                    if word:
                        self._store_pattern('word_removal', word, rule_id, conn)
                
                # Armazena padrões de adição de palavras
                for word in transformation.get('added_words', []):
                    if word:
                        self._store_pattern('word_addition', word, rule_id, conn)
                
                # Armazena substituições de palavras
                for replacement in transformation.get('word_replacements', []):
                    if replacement:
                        self._store_pattern('word_replacement', json.dumps(replacement), rule_id, conn)
            except Exception as e:
                # Se houver erro na análise, continua mesmo assim (a regra principal já foi salva)
                print(f"Erro ao analisar transformação para '{pattern_text}' -> '{target_text}': {e}")
            
            conn.commit()
        
        return rule_id
    
    def _store_pattern(self, pattern_type: str, pattern_data: str, rule_id: int, conn=None):
        """Armazena um padrão de transformação"""
        # Se uma conexão foi passada, usa ela; caso contrário, cria uma nova
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, frequency FROM transformation_patterns
                WHERE pattern_type = ? AND pattern_data = ?
            """, (pattern_type, pattern_data))
            
            existing = cursor.fetchone()
            
            if existing:
                pattern_id, frequency = existing
                cursor.execute("""
                    UPDATE transformation_patterns
                    SET frequency = frequency + 1
                    WHERE id = ?
                """, (pattern_id,))
            else:
                cursor.execute("""
                    INSERT INTO transformation_patterns (pattern_type, pattern_data, frequency)
                    VALUES (?, ?, 1)
                """, (pattern_type, pattern_data))
        else:
            # Cria nova conexão apenas se necessário
            with sqlite3.connect(self.db_path, timeout=10.0) as new_conn:
                cursor = new_conn.cursor()
                cursor.execute("""
                    SELECT id, frequency FROM transformation_patterns
                    WHERE pattern_type = ? AND pattern_data = ?
                """, (pattern_type, pattern_data))
                
                existing = cursor.fetchone()
                
                if existing:
                    pattern_id, frequency = existing
                    cursor.execute("""
                        UPDATE transformation_patterns
                        SET frequency = frequency + 1
                        WHERE id = ?
                    """, (pattern_id,))
                else:
                    cursor.execute("""
                        INSERT INTO transformation_patterns (pattern_type, pattern_data, frequency)
                        VALUES (?, ?, 1)
                    """, (pattern_type, pattern_data))
                
                new_conn.commit()
    
    def suggest_transformation(self, product_text: str) -> List[Dict]:
        """Sugere transformações baseadas em padrões aprendidos"""
        product_norm = self.normalize_text(product_text)
        suggestions = []
        
        # Busca todas as rejeições de uma vez para otimizar
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_text, suggested_text FROM rejected_patterns
            """)
            rejected_set = set(cursor.fetchall())
        
        def is_rejected_fast(original: str, suggested: str) -> bool:
            """Verifica rapidamente se está na lista de rejeições"""
            orig_norm = self.normalize_text(original)
            sugg_norm = self.normalize_text(suggested)
            return (orig_norm, sugg_norm) in rejected_set
        
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Busca regras exatas ou similares
            cursor.execute("""
                SELECT pattern_text, target_text, confidence, usage_count
                FROM learned_rules
                WHERE pattern_text LIKE ? OR ? LIKE '%' || pattern_text || '%'
                ORDER BY confidence DESC, usage_count DESC
                LIMIT 5
            """, (f'%{product_norm}%', product_norm))
            
            exact_matches = cursor.fetchall()
            
            for pattern, target, confidence, usage_count in exact_matches:
                if pattern in product_norm:
                    # Verifica se esta transformação foi rejeitada
                    if not is_rejected_fast(product_text, target):
                        suggestions.append({
                            'original': product_text,
                            'suggested': target,
                            'confidence': confidence,
                            'type': 'exact_match',
                            'usage_count': usage_count
                        })
            
            # Busca padrões de transformação aplicáveis
            product_words = set(product_norm.split())
            
            # Padrões de remoção de palavras
            cursor.execute("""
                SELECT pattern_data, frequency FROM transformation_patterns
                WHERE pattern_type = 'word_removal'
                ORDER BY frequency DESC
            """)
            
            removal_patterns = cursor.fetchall()
            for word, frequency in removal_patterns:
                if word in product_words:
                    # Tenta encontrar regra que remove essa palavra
                    cursor.execute("""
                        SELECT DISTINCT lr.target_text, lr.confidence
                        FROM learned_rules lr
                        JOIN transformation_patterns tp ON tp.pattern_data = ?
                        WHERE tp.pattern_type = 'word_removal'
                        AND lr.pattern_text LIKE '%' || ? || '%'
                        ORDER BY lr.confidence DESC
                        LIMIT 1
                    """, (word, word))
                    
                    result = cursor.fetchone()
                    if result:
                        target, conf = result
                        # Remove a palavra e aplica transformação
                        new_text = product_norm.replace(word, '').strip()
                        new_text = re.sub(r'\s+', ' ', new_text)
                        suggested_text = target if target else new_text.title()
                        
                        # Verifica se esta transformação foi rejeitada
                        if not is_rejected_fast(product_text, suggested_text):
                            suggestions.append({
                                'original': product_text,
                                'suggested': suggested_text,
                                'confidence': conf * 0.7,  # Reduz confiança para padrões inferidos
                                'type': 'pattern_based',
                                'usage_count': frequency
                            })
            
            # Padrões de adição de palavras
            cursor.execute("""
                SELECT pattern_data, frequency FROM transformation_patterns
                WHERE pattern_type = 'word_addition'
                ORDER BY frequency DESC
                LIMIT 3
            """)
            
            addition_patterns = cursor.fetchall()
            for word, frequency in addition_patterns:
                if word not in product_words:
                    # Busca regras que adicionam essa palavra
                    cursor.execute("""
                        SELECT DISTINCT lr.target_text, lr.confidence
                        FROM learned_rules lr
                        JOIN transformation_patterns tp ON tp.pattern_data = ?
                        WHERE tp.pattern_type = 'word_addition'
                        AND lr.target_text LIKE '%' || ? || '%'
                        ORDER BY lr.confidence DESC
                        LIMIT 1
                    """, (word, word))
                    
                    result = cursor.fetchone()
                    if result:
                        target, conf = result
                        suggested_text = f"{product_text} {word}".title()
                        
                        # Verifica se esta transformação foi rejeitada
                        if not is_rejected_fast(product_text, suggested_text):
                            suggestions.append({
                                'original': product_text,
                                'suggested': suggested_text,
                                'confidence': conf * 0.6,
                                'type': 'pattern_based',
                                'usage_count': frequency
                            })
        
        # Remove duplicatas e ordena por confiança
        # (as rejeições já foram filtradas acima)
        seen = set()
        unique_suggestions = []
        for sug in sorted(suggestions, key=lambda x: x['confidence'], reverse=True):
            key = (sug['original'], sug['suggested'])
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(sug)
        
        return unique_suggestions[:3]  # Retorna top 3
    
    def record_success(self, pattern_text: str, target_text: str):
        """Registra sucesso de uma transformação"""
        pattern_norm = self.normalize_text(pattern_text)
        target_norm = self.normalize_text(target_text)
        
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE learned_rules
                SET success_count = success_count + 1,
                    confidence = CAST(success_count + 1 AS REAL) / usage_count
                WHERE pattern_text = ? AND target_text = ?
            """, (pattern_norm, target_norm))
            
            conn.commit()
    
    def record_failure(self, pattern_text: str, target_text: str):
        """Registra falha de uma transformação e adiciona à lista de rejeições"""
        pattern_norm = self.normalize_text(pattern_text)
        target_norm = self.normalize_text(target_text)
        
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Atualiza a confiança da regra (se existir)
            cursor.execute("""
                UPDATE learned_rules
                SET confidence = CAST(success_count AS REAL) / (usage_count + 1)
                WHERE pattern_text = ? AND target_text = ?
            """, (pattern_norm, target_norm))
            
            # Adiciona à tabela de rejeições (ignora se já existir devido ao UNIQUE)
            cursor.execute("""
                INSERT OR IGNORE INTO rejected_patterns (original_text, suggested_text)
                VALUES (?, ?)
            """, (pattern_norm, target_norm))
            
            conn.commit()
    
    def is_rejected(self, original_text: str, suggested_text: str) -> bool:
        """Verifica se uma transformação foi rejeitada anteriormente"""
        original_norm = self.normalize_text(original_text)
        suggested_norm = self.normalize_text(suggested_text)
        
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM rejected_patterns
                WHERE original_text = ? AND suggested_text = ?
            """, (original_norm, suggested_norm))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_learned_patterns(self, limit: int = 20) -> List[Dict]:
        """Retorna padrões aprendidos mais usados"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, pattern_text, target_text, usage_count, success_count, confidence, last_used
                FROM learned_rules
                ORDER BY usage_count DESC, confidence DESC
                LIMIT ?
            """, (limit,))
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'id': row[0],
                    'pattern': row[1],
                    'target': row[2],
                    'usage_count': row[3],
                    'success_count': row[4],
                    'confidence': row[5],
                    'last_used': row[6]
                })
        
        return patterns

    def delete_learned_rule(self, rule_id: int):
        """Exclui uma regra aprendida pelo ID"""
        if not rule_id:
            return

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()

            # Remove a regra principal
            cursor.execute("""
                DELETE FROM learned_rules
                WHERE id = ?
            """, (rule_id,))

            # Também remove sugestões pendentes associadas, se houver
            cursor.execute("""
                DELETE FROM pending_suggestions
                WHERE pattern_id = ?
            """, (rule_id,))

            conn.commit()

