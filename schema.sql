-- My Beauty AI Database Schema
-- PostgreSQL database for cosmetic ingredient analysis and routine optimization

-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom enum types
CREATE TYPE skin_type_enum AS ENUM ('dry', 'oily', 'combination', 'sensitive', 'normal');
CREATE TYPE routine_time_enum AS ENUM ('morning', 'evening', 'both');
CREATE TYPE conflict_severity_enum AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE approval_status_enum AS ENUM ('approved', 'pending', 'restricted', 'banned');

-- =============================================================================
-- CORE ENTITIES
-- =============================================================================

-- Brands table
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL UNIQUE,
    brand_country VARCHAR(100),
    brand_website VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(500) NOT NULL,
    brand_id INTEGER REFERENCES brands(brand_id) ON DELETE CASCADE,
    image_url VARCHAR(1000),
    barcode VARCHAR(100) UNIQUE,
    ingredients_raw TEXT, -- Original ingredient list as text
    product_type VARCHAR(100), -- serum, moisturizer, cleanser, etc.
    price_usd DECIMAL(10,2),
    volume_ml INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for better performance
    CONSTRAINT unique_brand_product UNIQUE(brand_id, product_name)
);

-- Ingredients master table
CREATE TABLE ingredients (
    ingredient_id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE, -- Primary name
    inci_name VARCHAR(255), -- International Nomenclature of Cosmetic Ingredients
    korean_name VARCHAR(255), -- Korean name for KFDA data
    chinese_name VARCHAR(255), -- For international expansion
    cas_number VARCHAR(50), -- Chemical Abstracts Service number
    einecs_number VARCHAR(50), -- European chemical identifier

    -- Chemical properties
    molecular_formula VARCHAR(200),
    molecular_weight DECIMAL(10,4),
    ph_min DECIMAL(3,1),
    ph_max DECIMAL(3,1),

    -- Regulatory information
    regulatory_status approval_status_enum DEFAULT 'pending',
    max_concentration_face DECIMAL(5,2), -- Maximum allowed concentration for face
    max_concentration_eye DECIMAL(5,2), -- Maximum allowed concentration for eye area

    -- Classification
    function_primary VARCHAR(100), -- moisturizer, antioxidant, preservative, etc.
    function_secondary VARCHAR(100),
    ingredient_category VARCHAR(100), -- active, inactive, preservative, etc.

    -- Safety information
    is_comedogenic BOOLEAN DEFAULT FALSE,
    comedogenic_rating INTEGER CHECK (comedogenic_rating >= 0 AND comedogenic_rating <= 5),
    is_photosensitive BOOLEAN DEFAULT FALSE,
    pregnancy_safe BOOLEAN DEFAULT NULL, -- NULL means unknown/consult doctor

    -- Data source tracking
    data_source VARCHAR(100), -- KFDA_API, Manual, Import, etc.
    origin_definition TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product-Ingredients junction table with concentration tracking
CREATE TABLE product_ingredients (
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    concentration_percentage DECIMAL(5,2), -- Actual concentration if available
    concentration_range VARCHAR(50), -- e.g., "1-3%", "<0.5%"
    ingredient_order INTEGER, -- Order in ingredient list (lower = higher concentration)
    is_active BOOLEAN DEFAULT TRUE, -- Can be used to disable without deleting
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (product_id, ingredient_id)
);

-- =============================================================================
-- USER MANAGEMENT
-- =============================================================================

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    skin_type skin_type_enum,
    skin_concerns TEXT[], -- Array of concerns: acne, aging, pigmentation, etc.
    allergies TEXT[], -- Known allergic ingredients

    -- Preferences
    preferred_routine_complexity VARCHAR(20) DEFAULT 'moderate', -- minimal, moderate, extensive
    preferred_price_range VARCHAR(20) DEFAULT 'medium', -- budget, medium, luxury
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User routines
CREATE TABLE user_routines (
    routine_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    routine_name VARCHAR(255) NOT NULL,
    routine_time routine_time_enum NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_routine UNIQUE(user_id, routine_name, routine_time)
);

-- Routine steps (products in order)
CREATE TABLE routine_steps (
    step_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    routine_id UUID REFERENCES user_routines(routine_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    wait_minutes INTEGER DEFAULT 0, -- Time to wait before next step
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT unique_routine_step_order UNIQUE(routine_id, step_order)
);

-- =============================================================================
-- CONFLICT DETECTION SYSTEM
-- =============================================================================

-- Ingredient interaction rules
CREATE TABLE ingredient_conflicts (
    conflict_id SERIAL PRIMARY KEY,
    ingredient1_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    ingredient2_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,

    -- Conflict details
    conflict_type VARCHAR(50) NOT NULL, -- chemical, physical, effectiveness
    severity conflict_severity_enum NOT NULL,
    description TEXT NOT NULL,
    scientific_explanation TEXT,

    -- Conditions
    ph_dependent BOOLEAN DEFAULT FALSE,
    concentration_dependent BOOLEAN DEFAULT FALSE,
    time_dependent BOOLEAN DEFAULT FALSE, -- e.g., can use if separated by hours

    -- Recommendations
    recommended_separation_hours INTEGER, -- NULL means never combine
    alternative_suggestions TEXT,

    -- Evidence
    evidence_level VARCHAR(20) DEFAULT 'moderate', -- low, moderate, high, proven
    research_references TEXT[],

    -- Metadata
    verified_by_expert BOOLEAN DEFAULT FALSE,
    expert_id UUID, -- Reference to dermatologist/chemist who verified
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure we don't duplicate conflicts (A-B same as B-A)
    CONSTRAINT unique_ingredient_pair UNIQUE(LEAST(ingredient1_id, ingredient2_id), GREATEST(ingredient1_id, ingredient2_id))
);

-- Skin type specific sensitivities
CREATE TABLE skin_sensitivities (
    sensitivity_id SERIAL PRIMARY KEY,
    ingredient_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    skin_type skin_type_enum NOT NULL,
    sensitivity_level VARCHAR(20) NOT NULL, -- low, medium, high, avoid
    description TEXT,
    recommended_max_concentration DECIMAL(5,2),
    patch_test_required BOOLEAN DEFAULT TRUE,

    CONSTRAINT unique_ingredient_skin_type UNIQUE(ingredient_id, skin_type)
);

-- =============================================================================
-- KNOWLEDGE BASE FOR RAG SYSTEM
-- =============================================================================

-- Scientific documents and sources
CREATE TABLE knowledge_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(50), -- research_paper, clinical_study, regulatory_guideline
    source_url VARCHAR(1000),
    publication_date DATE,
    authors TEXT[],
    journal VARCHAR(200),
    doi VARCHAR(100),
    credibility_score INTEGER CHECK (credibility_score >= 1 AND credibility_score <= 10),

    -- For vector search
    embedding_vector VECTOR(1536), -- OpenAI ada-002 embedding size

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document-ingredient relationships
CREATE TABLE document_ingredients (
    document_id UUID REFERENCES knowledge_documents(document_id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) CHECK (relevance_score >= 0 AND relevance_score <= 1),

    PRIMARY KEY (document_id, ingredient_id)
);

-- =============================================================================
-- ANALYTICS AND OPTIMIZATION
-- =============================================================================

-- User routine performance tracking
CREATE TABLE routine_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    routine_id UUID REFERENCES user_routines(routine_id) ON DELETE CASCADE,

    -- User feedback
    effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
    skin_condition_improvement BOOLEAN,
    experienced_irritation BOOLEAN DEFAULT FALSE,
    ease_of_use_rating INTEGER CHECK (ease_of_use_rating >= 1 AND ease_of_use_rating <= 5),

    -- Usage tracking
    adherence_percentage DECIMAL(5,2), -- How often user follows the routine
    average_completion_time_minutes INTEGER,

    feedback_date DATE NOT NULL,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conflict prediction results tracking
CREATE TABLE conflict_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    product1_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    product2_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,

    predicted_conflict_severity conflict_severity_enum,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    prediction_explanation TEXT,

    -- User outcome
    user_proceeded BOOLEAN, -- Did user use products together despite warning?
    actual_outcome VARCHAR(50), -- no_issue, mild_irritation, severe_reaction, etc.
    user_feedback TEXT,

    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    outcome_date TIMESTAMP
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Products
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_type ON products(product_type);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;

-- Ingredients
CREATE INDEX idx_ingredients_name ON ingredients(ingredient_name);
CREATE INDEX idx_ingredients_inci ON ingredients(inci_name);
CREATE INDEX idx_ingredients_cas ON ingredients(cas_number) WHERE cas_number IS NOT NULL;
CREATE INDEX idx_ingredients_category ON ingredients(ingredient_category);
CREATE INDEX idx_ingredients_function ON ingredients(function_primary);
CREATE INDEX idx_ingredients_status ON ingredients(regulatory_status);

-- Product ingredients
CREATE INDEX idx_product_ingredients_product ON product_ingredients(product_id);
CREATE INDEX idx_product_ingredients_ingredient ON product_ingredients(ingredient_id);
CREATE INDEX idx_product_ingredients_concentration ON product_ingredients(concentration_percentage);

-- Users and routines
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_skin_type ON users(skin_type);
CREATE INDEX idx_user_routines_user_id ON user_routines(user_id);
CREATE INDEX idx_routine_steps_routine_id ON routine_steps(routine_id);
CREATE INDEX idx_routine_steps_order ON routine_steps(routine_id, step_order);

-- Conflicts
CREATE INDEX idx_ingredient_conflicts_ingredient1 ON ingredient_conflicts(ingredient1_id);
CREATE INDEX idx_ingredient_conflicts_ingredient2 ON ingredient_conflicts(ingredient2_id);
CREATE INDEX idx_ingredient_conflicts_severity ON ingredient_conflicts(severity);

-- Knowledge base
CREATE INDEX idx_knowledge_documents_type ON knowledge_documents(document_type);
CREATE INDEX idx_knowledge_documents_date ON knowledge_documents(publication_date);
-- Vector index for similarity search (specific to your vector extension)
-- CREATE INDEX idx_knowledge_documents_embedding ON knowledge_documents USING ivfflat (embedding_vector vector_cosine_ops);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- =============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_routines_updated_at BEFORE UPDATE ON user_routines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingredient_conflicts_updated_at BEFORE UPDATE ON ingredient_conflicts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_documents_updated_at BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SAMPLE DATA FOR TESTING
-- =============================================================================

-- Insert sample brands
INSERT INTO brands (brand_name, brand_country, brand_website) VALUES
('The Ordinary', 'Canada', 'https://theordinary.com'),
('Paula''s Choice', 'USA', 'https://paulaschoice.com'),
('Innisfree', 'South Korea', 'https://innisfree.com'),
('La Roche-Posay', 'France', 'https://laroche-posay.com'),
('Cetaphil', 'USA', 'https://cetaphil.com');

-- Insert sample ingredients
INSERT INTO ingredients (
    ingredient_name, inci_name, cas_number, function_primary, 
    ingredient_category, regulatory_status, is_comedogenic, ph_min, ph_max
) VALUES
('Niacinamide', 'Niacinamide', '98-92-0', 'antioxidant', 'active', 'approved', FALSE, 5.0, 7.0),
('Retinol', 'Retinol', '68-26-8', 'anti-aging', 'active', 'approved', FALSE, 5.5, 6.5),
('Salicylic Acid', 'Salicylic Acid', '69-72-7', 'exfoliant', 'active', 'approved', FALSE, 3.0, 4.0),
('Glycolic Acid', 'Glycolic Acid', '79-14-1', 'exfoliant', 'active', 'approved', FALSE, 2.0, 3.5),
('Hyaluronic Acid', 'Sodium Hyaluronate', '9067-32-7', 'moisturizer', 'active', 'approved', FALSE, 5.0, 8.0),
('Vitamin C', 'L-Ascorbic Acid', '50-81-7', 'antioxidant', 'active', 'approved', FALSE, 2.5, 3.5),
('Benzyl Alcohol', 'Benzyl Alcohol', '100-51-6', 'preservative', 'inactive', 'approved', FALSE, NULL, NULL);

-- Insert sample conflict rules
INSERT INTO ingredient_conflicts (
    ingredient1_id, ingredient2_id, conflict_type, severity, description, 
    scientific_explanation, recommended_separation_hours
) VALUES
(
    (SELECT ingredient_id FROM ingredients WHERE ingredient_name = 'Retinol'),
    (SELECT ingredient_id FROM ingredients WHERE ingredient_name = 'Vitamin C'),
    'chemical', 'medium',
    'Retinol and Vitamin C can potentially irritate skin when used together',
    'Both are potent actives that can increase photosensitivity and cause irritation in sensitive individuals',
    12
),
(
    (SELECT ingredient_id FROM ingredients WHERE ingredient_name = 'Retinol'),
    (SELECT ingredient_id FROM ingredients WHERE ingredient_name = 'Salicylic Acid'),
    'chemical', 'high',
    'Combining retinol with salicylic acid increases risk of severe irritation and over-exfoliation',
    'Both ingredients increase cell turnover and can compromise skin barrier when used simultaneously',
    24
);

-- Create views for commonly used queries
CREATE VIEW product_summary AS
SELECT 
    p.product_id,
    p.product_name,
    b.brand_name,
    p.product_type,
    COUNT(pi.ingredient_id) as ingredient_count,
    p.price_usd,
    p.created_at
FROM products p
JOIN brands b ON p.brand_id = b.brand_id
LEFT JOIN product_ingredients pi ON p.product_id = pi.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, b.brand_name;

CREATE VIEW ingredient_usage_stats AS
SELECT 
    i.ingredient_id,
    i.ingredient_name,
    i.inci_name,
    i.function_primary,
    COUNT(pi.product_id) as used_in_products,
    AVG(pi.concentration_percentage) as avg_concentration
FROM ingredients i
LEFT JOIN product_ingredients pi ON i.ingredient_id = pi.ingredient_id
GROUP BY i.ingredient_id, i.ingredient_name, i.inci_name, i.function_primary;

-- Grant permissions (adjust as needed for your application user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mybeauty_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mybeauty_app;

COMMIT;
