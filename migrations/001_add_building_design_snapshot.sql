-- Apply once to existing MySQL databases before deploying the design API.
-- Fresh databases receive these columns from SQLAlchemy's create_all().
ALTER TABLE buildings
  ADD COLUMN design_snapshot JSON NULL,
  ADD COLUMN design_version INT NOT NULL DEFAULT 0;
