export type ChunkType = "text" | "table" | "figure" | "equation";

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  page: number;
}

export interface ExtractedElement {
  id: string;
  element_id?: string; // alias
  element_type: string;
  content: string;
  text?: string; // alias
  page_number: number;
  confidence?: number;
  bounding_box?: BoundingBox;
}

export interface SemanticChunk {
  id: string;
  chunk_id?: string; // alias
  doc_id: string;
  chunk_type: ChunkType;
  content: string;
  page_number: number;
  section?: string;
  bounding_box?: BoundingBox;
}

export interface TableCell {
  row: number;
  col: number;
  row_span?: number;
  col_span?: number;
  content: string;
  is_header?: boolean;
}

export interface ExtractedTable {
  id: string;
  table_id?: string; // alias
  page_number: number;
  caption?: string;
  image_path?: string;
  rows?: number;
  cols?: number;
  cells: TableCell[];
  csv_repr?: string;
  bounding_box?: BoundingBox;
}

export interface ExtractedFigure {
  id: string;
  figure_id?: string; // alias
  page_number: number;
  caption?: string;
  image_path?: string;
  figure_type?: string;
  bounding_box?: BoundingBox;
}

export interface ExtractedEquation {
  id: string;
  equation_id?: string; // alias
  page_number: number;
  raw_text: string;
  latex?: string;
  latex_expression?: string; // alias
  explanation?: string;
  variables?: string[];
  is_inline?: boolean;
  bounding_box?: BoundingBox;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "failed";
  page_count: number;
  title?: string;
  authors: string[];
  element_count: number;
  table_count: number;
  figure_count: number;
  equation_count: number;
  chunk_count: number;
  upload_timestamp?: string;
}

export interface FullDocumentData {
  id: string;
  filename: string;
  status: string;
  metadata: {
    page_count: number;
    title?: string;
    authors?: string[];
    creation_date?: string;
    file_size_bytes?: number;
  };
  elements: ExtractedElement[];
  tables: ExtractedTable[];
  figures: ExtractedFigure[];
  equations: ExtractedEquation[];
  chunks: SemanticChunk[];
  references?: any[];
  citations?: any[];
  graph_stats?: {
    node_count: number;
    edge_count: number;
  };
}

export interface CitationEvidence {
  source_id: string;
  doc_id: string;
  page_number: number;
  section?: string;
  chunk_type: ChunkType;
  snippet: string;
  bounding_box?: BoundingBox;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  confidence_score: number;
  citations: CitationEvidence[];
  chunks_retrieved: number;
  agent_path?: string[];
}

export interface SamplePaper {
  id: string;
  title: string;
  authors: string;
  year: string;
  venue: string;
  abstract: string;
  filename: string;
  size: string;
  pages: number;
  tables: number;
  figures: number;
  equations: number;
  tags: string[];
}
