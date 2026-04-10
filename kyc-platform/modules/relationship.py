"""
Motor de Análisis de Relaciones
===============================
Construye grafo de conocimiento y detecta patrones sospechosos
"""

import os
import logging
from typing import Dict, Any, List, Optional
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)

class RelationshipEngine:
    """Motor de análisis de red y relaciones"""
    
    def __init__(self):
        self.use_neo4j = os.getenv("USE_NEO4J", "false").lower() == "true"
        
        if self.use_neo4j:
            # Usar Neo4j
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info("Usando Neo4j como backend de grafo")
        else:
            # Usar NetworkX (en memoria)
            self.graph = nx.Graph()
            logger.info("Usando NetworkX como backend de grafo")
    
    async def ingest_person(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        curp: Optional[str] = None,
        rfc: Optional[str] = None,
        address: Optional[str] = None,
        risk_score: float = 0,
        risk_level: str = "BAJO"
    ) -> Dict[str, Any]:
        """Ingresa una persona al grafo"""
        
        person_id = f"person_{curp or name.replace(' ', '_')}"
        
        if self.use_neo4j:
            return await self._ingest_person_neo4j(
                person_id, name, email, phone, curp, rfc, address, risk_score, risk_level
            )
        else:
            return await self._ingest_person_networkx(
                person_id, name, email, phone, curp, rfc, address, risk_score, risk_level
            )
    
    async def _ingest_person_networkx(
        self, person_id, name, email, phone, curp, rfc, address, risk_score, risk_level
    ):
        """Ingesta en NetworkX"""
        
        # Agregar nodo de persona
        self.graph.add_node(
            person_id,
            type="Person",
            name=name,
            risk_score=risk_score,
            risk_level=risk_level,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Agregar atributos y relaciones
        if email:
            email_id = f"email_{email}"
            self.graph.add_node(email_id, type="Email", value=email)
            self.graph.add_edge(person_id, email_id, relationship="HAS_EMAIL")
        
        if phone:
            phone_id = f"phone_{phone}"
            self.graph.add_node(phone_id, type="Phone", value=phone)
            self.graph.add_edge(person_id, phone_id, relationship="HAS_PHONE")
        
        if curp:
            curp_id = f"curp_{curp}"
            self.graph.add_node(curp_id, type="CURP", value=curp)
            self.graph.add_edge(person_id, curp_id, relationship="HAS_CURP")
        
        if rfc:
            rfc_id = f"rfc_{rfc}"
            self.graph.add_node(rfc_id, type="RFC", value=rfc)
            self.graph.add_edge(person_id, rfc_id, relationship="HAS_RFC")
        
        if address:
            addr_id = f"address_{hash(address)}"
            self.graph.add_node(addr_id, type="Address", value=address)
            self.graph.add_edge(person_id, addr_id, relationship="HAS_ADDRESS")
        
        logger.info(f"Persona ingresada al grafo: {person_id}")
        
        return {
            "id": person_id,
            "name": name,
            "nodes_created": 1,
            "relationships_created": sum([email is not None, phone is not None, 
                                         curp is not None, rfc is not None, 
                                         address is not None])
        }
    
    async def _ingest_person_neo4j(
        self, person_id, name, email, phone, curp, rfc, address, risk_score, risk_level
    ):
        """Ingesta en Neo4j"""
        
        with self.driver.session() as session:
            # Crear persona
            result = session.run("""
                MERGE (p:Person {id: $id})
                SET p.name = $name,
                    p.risk_score = $risk_score,
                    p.risk_level = $risk_level,
                    p.updated_at = datetime()
                RETURN p
            """, id=person_id, name=name, risk_score=risk_score, risk_level=risk_level)
            
            # Crear atributos
            relationships_created = 0
            
            if email:
                session.run("""
                    MATCH (p:Person {id: $person_id})
                    MERGE (e:Email {value: $email})
                    MERGE (p)-[:HAS_EMAIL]->(e)
                """, person_id=person_id, email=email)
                relationships_created += 1
            
            if phone:
                session.run("""
                    MATCH (p:Person {id: $person_id})
                    MERGE (ph:Phone {value: $phone})
                    MERGE (p)-[:HAS_PHONE]->(ph)
                """, person_id=person_id, phone=phone)
                relationships_created += 1
            
            if curp:
                session.run("""
                    MATCH (p:Person {id: $person_id})
                    MERGE (c:CURP {value: $curp})
                    MERGE (p)-[:HAS_CURP]->(c)
                """, person_id=person_id, curp=curp)
                relationships_created += 1
            
            logger.info(f"Persona ingresada a Neo4j: {person_id}")
        
        return {
            "id": person_id,
            "name": name,
            "nodes_created": 1,
            "relationships_created": relationships_created
        }
    
    async def analyze_network(self, person_id: str, depth: int = 2) -> Dict[str, Any]:
        """Analiza la red de relaciones de una persona"""
        
        if self.use_neo4j:
            return await self._analyze_network_neo4j(person_id, depth)
        else:
            return await self._analyze_network_networkx(person_id, depth)
    
    async def _analyze_network_networkx(self, person_id: str, depth: int):
        """Análisis con NetworkX"""
        
        if person_id not in self.graph:
            return {
                "person_id": person_id,
                "connected_persons": 0,
                "suspicious_patterns": [],
                "high_risk_connections": 0,
                "network_size": 0
            }
        
        # BFS para encontrar nodos hasta depth
        visited = set()
        queue = [(person_id, 0)]
        network_nodes = []
        
        while queue:
            node, d = queue.pop(0)
            if node in visited or d > depth:
                continue
            
            visited.add(node)
            network_nodes.append(node)
            
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))
        
        # Buscar personas conectadas
        connected_persons = [
            n for n in network_nodes 
            if n != person_id and self.graph.nodes[n].get("type") == "Person"
        ]
        
        # Detectar patrones sospechosos
        suspicious_patterns = []
        
        # Patrón 1: Mismo email/teléfono/dirección compartido por múltiples personas
        for node in network_nodes:
            node_data = self.graph.nodes[node]
            if node_data.get("type") in ["Email", "Phone", "Address"]:
                # Contar cuántas personas comparten este atributo
                persons_with_attr = [
                    n for n in self.graph.neighbors(node)
                    if self.graph.nodes[n].get("type") == "Person"
                ]
                
                if len(persons_with_attr) >= 2:
                    suspicious_patterns.append({
                        "type": "SHARED_ATTRIBUTE",
                        "description": f"{len(persons_with_attr)} personas comparten el mismo {node_data['type']}: {node_data.get('value', 'N/A')}",
                        "severity": "MEDIUM" if len(persons_with_attr) == 2 else "HIGH",
                        "entities": persons_with_attr
                    })
        
        # Patrón 2: Conexión con persona de alto riesgo
        high_risk_connections = sum(
            1 for p in connected_persons
            if self.graph.nodes[p].get("risk_level") in ["ALTO", "CRÍTICO"]
        )
        
        if high_risk_connections > 0:
            suspicious_patterns.append({
                "type": "HIGH_RISK_CONNECTION",
                "description": f"Conectado con {high_risk_connections} persona(s) de alto riesgo",
                "severity": "HIGH",
                "count": high_risk_connections
            })
        
        return {
            "person_id": person_id,
            "connected_persons": len(connected_persons),
            "suspicious_patterns": suspicious_patterns,
            "high_risk_connections": high_risk_connections,
            "network_size": len(network_nodes),
            "depth": depth
        }
    
    async def _analyze_network_neo4j(self, person_id: str, depth: int):
        """Análisis con Neo4j"""
        
        with self.driver.session() as session:
            # Encontrar red
            result = session.run("""
                MATCH path = (p:Person {id: $person_id})-[*1..%d]-(connected)
                RETURN DISTINCT connected
                LIMIT 1000
            """ % (depth * 2), person_id=person_id)
            
            network_nodes = [record["connected"] for record in result]
            
            # Contar personas conectadas
            connected_persons = len([
                n for n in network_nodes 
                if "Person" in n.labels and n["id"] != person_id
            ])
            
            # Patrones sospechosos (simplificado)
            suspicious_patterns = []
            high_risk_connections = 0
            
            return {
                "person_id": person_id,
                "connected_persons": connected_persons,
                "suspicious_patterns": suspicious_patterns,
                "high_risk_connections": high_risk_connections,
                "network_size": len(network_nodes),
                "depth": depth
            }
    
    async def export_visualization(
        self, 
        person_id: str, 
        depth: int = 2
    ) -> Dict[str, Any]:
        """Exporta datos para Cytoscape.js"""
        
        if self.use_neo4j:
            return await self._export_neo4j(person_id, depth)
        else:
            return await self._export_networkx(person_id, depth)
    
    async def _export_networkx(self, person_id: str, depth: int):
        """Exporta NetworkX a formato Cytoscape"""
        
        if person_id not in self.graph:
            return {"elements": {"nodes": [], "edges": []}}
        
        # BFS
        visited = set()
        queue = [(person_id, 0)]
        subgraph_nodes = set()
        
        while queue:
            node, d = queue.pop(0)
            if node in visited or d > depth:
                continue
            
            visited.add(node)
            subgraph_nodes.add(node)
            
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))
        
        # Crear subgrafo
        subgraph = self.graph.subgraph(subgraph_nodes)
        
        # Convertir a Cytoscape
        nodes = []
        for node in subgraph.nodes():
            data = subgraph.nodes[node]
            nodes.append({
                "data": {
                    "id": node,
                    "label": data.get("name") or data.get("value") or node,
                    "type": data.get("type", "Unknown"),
                    "risk_level": data.get("risk_level"),
                    "risk_score": data.get("risk_score")
                }
            })
        
        edges = []
        for source, target in subgraph.edges():
            edge_data = subgraph.get_edge_data(source, target)
            edges.append({
                "data": {
                    "source": source,
                    "target": target,
                    "relationship": edge_data.get("relationship", "RELATED_TO")
                }
            })
        
        return {
            "elements": {
                "nodes": nodes,
                "edges": edges
            },
            "layout": {
                "name": "cose",
                "animate": True
            }
        }
    
    async def _export_neo4j(self, person_id: str, depth: int):
        """Exporta Neo4j a formato Cytoscape"""
        
        with self.driver.session() as session:
            # Obtener subgrafo
            result = session.run("""
                MATCH path = (p:Person {id: $person_id})-[*1..%d]-(connected)
                RETURN path
                LIMIT 100
            """ % (depth * 2), person_id=person_id)
            
            nodes = []
            edges = []
            seen_nodes = set()
            seen_edges = set()
            
            for record in result:
                path = record["path"]
                
                # Procesar nodos
                for node in path.nodes:
                    node_id = node.element_id
                    if node_id not in seen_nodes:
                        seen_nodes.add(node_id)
                        nodes.append({
                            "data": {
                                "id": node_id,
                                "label": node.get("name") or node.get("value") or "Unknown",
                                "type": list(node.labels)[0] if node.labels else "Unknown"
                            }
                        })
                
                # Procesar relaciones
                for rel in path.relationships:
                    edge_id = f"{rel.start_node.element_id}_{rel.end_node.element_id}"
                    if edge_id not in seen_edges:
                        seen_edges.add(edge_id)
                        edges.append({
                            "data": {
                                "source": rel.start_node.element_id,
                                "target": rel.end_node.element_id,
                                "relationship": rel.type
                            }
                        })
            
            return {
                "elements": {
                    "nodes": nodes,
                    "edges": edges
                },
                "layout": {
                    "name": "cose",
                    "animate": True
                }
            }
    
    def __del__(self):
        """Cerrar conexión Neo4j si existe"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
