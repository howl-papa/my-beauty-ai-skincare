-- My Beauty AI Database Schema
-- PostgreSQL database schema for cosmetic ingredient analysis system

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enum types for better data integrity
CREATE TYPE skin_type_enum AS ENUM ('oily', 'dry', 'combination', 'sensitive', 'normal');
CREATE TYPE product_category_enum AS ENUM (
    'cleanser', 'toner', 'essence', 'serum', 'moisturizer', 'sunscreen', 
    'treatment', 'mask', 'exfoliant', 'oil', 'mist', 'eye_cream'
);
CREATE TYPE severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE routine_time_enum AS ENUM ('morning', 'evening', 'both');

-- BRANDS table - Store cosmetic brand information
CREATE TABLE brands (
    brand_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100),
    website VARCHAR(500),
    description TEXT,
    founded_year INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INGREDIENTS table - Comprehensive ingredient database
CREATE TABLE ingredients (
    ingredient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    inci_name VARCHAR(255), -- International Nomenclature of Cosmetic Ingredients
    cas_number VARCHAR(50), -- Chemical Abstracts Service number
    category VARCHAR(100), -- e.g., 'Active', 'Preservative', 'Emollient'
    function_type VARCHAR(100), -- e.g., 'Anti-aging', 'Moisturizing', 'Exfoliating'
    molecular_weight DECIMAL(10,4),
    ph_range_min DECIMAL(3,1),
    ph_range_max DECIMAL(3,1),
    solubility VARCHAR(100), -- e.g., 'Water-soluble', 'Oil-soluble'
    description TEXT,
    benefits TEXT,
    side_effects TEXT,
    concentration_range_min DECIMAL(5,2), -- Recommended minimum concentration %
    concentration_range_max DECIMAL(5,2), -- Recommended maximum concentration %
    embedding vector(1536), -- For RAG similarity search (OpenAI embedding size)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PRODUCTS table - Store cosmetic product information
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID NOT NULL REFERENCES brands(brand_id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    category product_category_enum NOT NULL,
    subcategory VARCHAR(100),
    price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    volume_ml INTEGER,
    description TEXT,
    instructions TEXT,
    ph_level DECIMAL(3,1),
    suitable_skin_types skin_type_enum[],
    target_concerns TEXT[], -- Array of concerns like 'acne', 'wrinkles', 'dark_spots'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT positive_price CHECK (price >= 0),
    CONSTRAINT positive_volume CHECK (volume_ml > 0)
);

-- PRODUCT_INGREDIENTS table - Many-to-many relationship with concentration info
CREATE TABLE product_ingredients (
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    concentration DECIMAL(5,2), -- Concentration percentage (0.00 to 100.00)
    ingredient_order INTEGER, -- Order in ingredient list (1 = first ingredient)
    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (product_id, ingredient_id),
    CONSTRAINT valid_concentration CHECK (concentration >= 0 AND concentration <= 100),
    CONSTRAINT positive_order CHECK (ingredient_order > 0)
);

-- CONFLICT_RULES table - Predefined ingredient conflict rules
CREATE TABLE conflict_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingredient1_id UUID NOT NULL REFERENCES ingredients(ingredient_id),
    ingredient2_id UUID NOT NULL REFERENCES ingredients(ingredient_id),
    severity severity_enum NOT NULL DEFAULT 'MEDIUM',
    description TEXT NOT NULL,
    scientific_basis TEXT, -- Research or reasoning behind the conflict
    affected_skin_types skin_type_enum[],
    time_separation_hours INTEGER, -- Recommended hours between applications
    ph_conflict BOOLEAN DEFAULT false,
    concentration_limit DECIMAL(5,2), -- Max safe combined concentration
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT different_ingredients CHECK (ingredient1_id != ingredient2_id),
    CONSTRAINT valid_separation CHECK (time_separation_hours >= 0)
);

-- USER_PROFILES table - Store user skin profiles and preferences
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skin_type skin_type_enum NOT NULL,
    skin_concerns TEXT[], -- Array of concerns
    sensitivity_level VARCHAR(20) DEFAULT 'moderate', -- 'low', 'moderate', 'high'
    allergies TEXT[], -- Known ingredient allergies
    age_range VARCHAR(20), -- e.g., '25-30', '30-35'
    climate VARCHAR(50), -- e.g., 'humid', 'dry', 'temperate'
    current_routine JSONB, -- Flexible storage for current routine data
    preferences JSONB, -- User preferences (brand preferences, price range, etc.)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ROUTINE_LOGS table - Track user routines and analysis history
CREATE TABLE routine_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- For anonymous users
    routine_data JSONB NOT NULL, -- Products and application times
    conflict_analysis JSONB, -- Results of conflict analysis
    optimization_suggestions JSONB, -- AI-generated suggestions
    rag_insights JSONB, -- Insights from RAG system
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT user_or_session CHECK (user_id IS NOT NULL OR session_id IS NOT NULL)
);

-- RAG_DOCUMENTS table - Store processed documents for RAG system
CREATE TABLE rag_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(500), -- URL, book title, paper reference
    document_type VARCHAR(100), -- 'research_paper', 'ingredient_guide', 'safety_data'
    category VARCHAR(100), -- 'ingredient_interaction', 'safety', 'efficacy'
    author VARCHAR(255),
    publication_date DATE,
    embedding vector(1536), -- Document embedding for similarity search
    metadata JSONB, -- Additional flexible metadata
    is_processed BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ANALYSIS_CACHE table - Cache expensive analysis results
CREATE TABLE analysis_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL, -- Hash of input parameters
    analysis_type VARCHAR(100) NOT NULL, -- 'conflict_analysis', 'routine_optimization'
    input_data JSONB NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- SYSTEM_LOGS table - System activity and error logging
CREATE TABLE system_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL, -- 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component VARCHAR(100), -- 'rag_system', 'conflict_analyzer', 'api'
    message TEXT NOT NULL,
    details JSONB,
    user_id UUID REFERENCES user_profiles(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_inci ON ingredients(inci_name);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE INDEX idx_ingredients_embedding ON ingredients USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_skin_types ON products USING gin(suitable_skin_types);
CREATE INDEX idx_products_concerns ON products USING gin(target_concerns);

CREATE INDEX idx_product_ingredients_product ON product_ingredients(product_id);
CREATE INDEX idx_product_ingredients_ingredient ON product_ingredients(ingredient_id);
CREATE INDEX idx_product_ingredients_order ON product_ingredients(ingredient_order);

CREATE INDEX idx_conflict_rules_ingredient1 ON conflict_rules(ingredient1_id);
CREATE INDEX idx_conflict_rules_ingredient2 ON conflict_rules(ingredient2_id);
CREATE INDEX idx_conflict_rules_severity ON conflict_rules(severity);

CREATE INDEX idx_user_profiles_skin_type ON user_profiles(skin_type);
CREATE INDEX idx_user_profiles_concerns ON user_profiles USING gin(skin_concerns);

CREATE INDEX idx_routine_logs_user ON routine_logs(user_id);
CREATE INDEX idx_routine_logs_session ON routine_logs(session_id);
CREATE INDEX idx_routine_logs_created ON routine_logs(created_at);

CREATE INDEX idx_rag_documents_type ON rag_documents(document_type);
CREATE INDEX idx_rag_documents_category ON rag_documents(category);
CREATE INDEX idx_rag_documents_embedding ON rag_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_analysis_cache_key ON analysis_cache(cache_key);
CREATE INDEX idx_analysis_cache_type ON analysis_cache(analysis_type);
CREATE INDEX idx_analysis_cache_expires ON analysis_cache(expires_at);

CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_component ON system_logs(component);
CREATE INDEX idx_system_logs_created ON system_logs(created_at);

-- Create update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conflict_rules_updated_at BEFORE UPDATE ON conflict_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rag_documents_updated_at BEFORE UPDATE ON rag_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data inserts for testing
INSERT INTO brands (name, country, website, description) VALUES 
('The Ordinary', 'Canada', 'https://theordinary.com', 'Clinical formulations with integrity'),
('Paula''s Choice', 'USA', 'https://paulaschoice.com', 'Research-driven skincare solutions'),
('CeraVe', 'USA', 'https://cerave.com', 'Developed with dermatologists'),
('La Roche-Posay', 'France', 'https://laroche-posay.com', 'Dermatological expertise');

INSERT INTO ingredients (name, inci_name, category, function_type, description, benefits) VALUES 
('Niacinamide', 'Niacinamide', 'Active', 'Multi-functional', 'Vitamin B3 derivative', 'Reduces pore appearance, regulates oil production'),
('Salicylic Acid', 'Salicylic Acid', 'Active', 'Exfoliant', 'Beta hydroxy acid (BHA)', 'Unclogs pores, reduces acne'),
('Retinol', 'Retinol', 'Active', 'Anti-aging', 'Vitamin A derivative', 'Stimulates cell turnover, reduces wrinkles'),
('L-Ascorbic Acid', 'L-Ascorbic Acid', 'Active', 'Antioxidant', 'Pure Vitamin C', 'Brightens skin, antioxidant protection'),
('Hyaluronic Acid', 'Sodium Hyaluronate', 'Active', 'Humectant', 'Hydrating molecule', 'Retains moisture, plumps skin');

INSERT INTO conflict_rules (ingredient1_id, ingredient2_id, severity, description, time_separation_hours) VALUES 
((SELECT ingredient_id FROM ingredients WHERE name = 'Retinol'),
 (SELECT ingredient_id FROM ingredients WHERE name = 'L-Ascorbic Acid'),
 'MEDIUM', 'Vitamin C may reduce retinol stability and effectiveness', 12),
((SELECT ingredient_id FROM ingredients WHERE name = 'Retinol'),
 (SELECT ingredient_id FROM ingredients WHERE name = 'Salicylic Acid'),
 'HIGH', 'Combined use may cause excessive irritation and dryness', 24);

-- Views for common queries
CREATE VIEW product_details AS
SELECT 
    p.product_id,
    p.name as product_name,
    b.name as brand_name,
    p.category,
    p.price,
    p.suitable_skin_types,
    p.target_concerns,
    array_agg(i.name ORDER BY pi.ingredient_order) as ingredients,
    array_agg(pi.concentration ORDER BY pi.ingredient_order) as concentrations
FROM products p
JOIN brands b ON p.brand_id = b.brand_id
LEFT JOIN product_ingredients pi ON p.product_id = pi.product_id
LEFT JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
WHERE p.is_active = true AND (pi.is_active = true OR pi.is_active IS NULL)
GROUP BY p.product_id, p.name, b.name, p.category, p.price, p.suitable_skin_types, p.target_concerns;

CREATE VIEW conflict_matrix AS
SELECT 
    i1.name as ingredient1_name,
    i2.name as ingredient2_name,
    cr.severity,
    cr.description,
    cr.time_separation_hours,
    cr.affected_skin_types
FROM conflict_rules cr
JOIN ingredients i1 ON cr.ingredient1_id = i1.ingredient_id
JOIN ingredients i2 ON cr.ingredient2_id = i2.ingredient_id
WHERE cr.is_active = true;

-- Comments for documentation
COMMENT ON TABLE brands IS 'Cosmetic brand information and metadata';
COMMENT ON TABLE products IS 'Product catalog with categorization and skin type targeting';
COMMENT ON TABLE ingredients IS 'Comprehensive ingredient database with chemical and functional properties';
COMMENT ON TABLE product_ingredients IS 'Junction table linking products to ingredients with concentration data';
COMMENT ON TABLE conflict_rules IS 'Predefined rules for ingredient interactions and conflicts';
COMMENT ON TABLE user_profiles IS 'User skin profiles and personalization preferences';
COMMENT ON TABLE routine_logs IS 'Historical tracking of user routines and AI analysis results';
COMMENT ON TABLE rag_documents IS 'Document storage for RAG knowledge base system';
COMMENT ON TABLE analysis_cache IS 'Performance optimization cache for expensive AI operations';
COMMENT ON TABLE system_logs IS 'System activity logging for debugging and monitoring';
