CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('estudiante', 'docente', 'administrador')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(160) NOT NULL,
    description TEXT,
    initial_investment NUMERIC(16,2) NOT NULL,
    discount_rate NUMERIC(8,6) NOT NULL,
    tax_rate NUMERIC(8,6) NOT NULL,
    horizon_years INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cash_flows (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year_number INT NOT NULL,
    sales NUMERIC(16,2),
    cost_of_sales NUMERIC(16,2),
    admin_expenses NUMERIC(16,2),
    selling_expenses NUMERIC(16,2),
    depreciation NUMERIC(16,2),
    taxes NUMERIC(16,2),
    net_income NUMERIC(16,2),
    free_cash_flow NUMERIC(16,2) NOT NULL
);

CREATE TABLE financial_indicators (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    npv NUMERIC(16,2),
    irr NUMERIC(10,6),
    immediate_liquidity_ratio NUMERIC(10,4),
    net_profit_margin NUMERIC(10,6),
    roa NUMERIC(10,6),
    roe NUMERIC(10,6),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensitivity_scenarios (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scenario_name VARCHAR(80) NOT NULL,
    variable_name VARCHAR(80) NOT NULL,
    variation_percentage NUMERIC(10,4) NOT NULL,
    npv_result NUMERIC(16,2),
    irr_result NUMERIC(10,6),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
