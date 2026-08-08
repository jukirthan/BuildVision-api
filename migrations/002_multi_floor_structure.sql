-- BuildVision multi-floor structure persistence.
-- Run with the application stopped, or through the project's migration runner.
-- Fresh databases are covered by the SQLAlchemy models; these statements
-- upgrade databases created before stable client IDs were introduced.

ALTER TABLE floors ADD COLUMN client_id VARCHAR(36) NULL;
ALTER TABLE floors ADD COLUMN elevation DOUBLE NOT NULL DEFAULT 0;
UPDATE floors SET client_id = UUID() WHERE client_id IS NULL OR client_id = '';
ALTER TABLE floors MODIFY COLUMN client_id VARCHAR(36) NOT NULL;
ALTER TABLE floors ADD CONSTRAINT uq_floor_building_number UNIQUE (building_id, floor_number);
ALTER TABLE floors ADD CONSTRAINT uq_floor_building_client UNIQUE (building_id, client_id);

ALTER TABLE pillars ADD COLUMN client_id VARCHAR(36) NULL;
ALTER TABLE pillars ADD COLUMN stack_id VARCHAR(100) NULL;
ALTER TABLE pillars ADD COLUMN base_elevation DOUBLE NOT NULL DEFAULT 0;
ALTER TABLE pillars ADD COLUMN concrete_grade VARCHAR(20) NOT NULL DEFAULT 'M25';
ALTER TABLE pillars ADD COLUMN steel_grade VARCHAR(20) NOT NULL DEFAULT 'Fe500';
ALTER TABLE pillars ADD COLUMN clear_cover_mm DOUBLE NOT NULL DEFAULT 40;
ALTER TABLE pillars ADD COLUMN shape VARCHAR(30) NOT NULL DEFAULT 'square';
ALTER TABLE pillars ADD COLUMN rotation_deg DOUBLE NOT NULL DEFAULT 0;
ALTER TABLE pillars ADD COLUMN reinforcement JSON NULL;
ALTER TABLE pillars ADD COLUMN loads JSON NULL;
ALTER TABLE pillars ADD COLUMN check_result JSON NULL;
UPDATE pillars SET client_id = UUID() WHERE client_id IS NULL OR client_id = '';
UPDATE pillars SET stack_id = CONCAT('legacy-stack-', id) WHERE stack_id IS NULL OR stack_id = '';
ALTER TABLE pillars MODIFY COLUMN client_id VARCHAR(36) NOT NULL;
ALTER TABLE pillars ADD INDEX ix_pillars_client_id (client_id);
ALTER TABLE pillars ADD INDEX ix_pillars_stack_id (stack_id);
ALTER TABLE pillars ADD CONSTRAINT uq_pillar_floor_client UNIQUE (floor_id, client_id);

ALTER TABLE beams ADD COLUMN client_id VARCHAR(36) NULL;
ALTER TABLE beams ADD COLUMN start_pillar_id INT NULL;
ALTER TABLE beams ADD COLUMN end_pillar_id INT NULL;
ALTER TABLE beams ADD COLUMN concrete_grade VARCHAR(20) NOT NULL DEFAULT 'M25';
ALTER TABLE beams ADD COLUMN steel_grade VARCHAR(20) NOT NULL DEFAULT 'Fe500';
ALTER TABLE beams ADD COLUMN reinforcement JSON NULL;
ALTER TABLE beams ADD COLUMN support_condition VARCHAR(30) NOT NULL DEFAULT 'continuous';
ALTER TABLE beams ADD COLUMN loads JSON NULL;
ALTER TABLE beams ADD COLUMN check_result JSON NULL;
UPDATE beams SET client_id = UUID() WHERE client_id IS NULL OR client_id = '';
ALTER TABLE beams MODIFY COLUMN client_id VARCHAR(36) NOT NULL;
ALTER TABLE beams ADD INDEX ix_beams_client_id (client_id);
ALTER TABLE beams ADD CONSTRAINT uq_beam_floor_client UNIQUE (floor_id, client_id);
ALTER TABLE beams ADD CONSTRAINT fk_beams_start_pillar FOREIGN KEY (start_pillar_id) REFERENCES pillars(id) ON DELETE CASCADE;
ALTER TABLE beams ADD CONSTRAINT fk_beams_end_pillar FOREIGN KEY (end_pillar_id) REFERENCES pillars(id) ON DELETE CASCADE;

ALTER TABLE slabs ADD COLUMN client_id VARCHAR(36) NULL;
ALTER TABLE slabs ADD COLUMN system VARCHAR(30) NOT NULL DEFAULT 'two_way';
ALTER TABLE slabs ADD COLUMN reinforcement_data JSON NULL;
ALTER TABLE slabs ADD COLUMN loads JSON NULL;
ALTER TABLE slabs ADD COLUMN check_result JSON NULL;
UPDATE slabs SET client_id = UUID() WHERE client_id IS NULL OR client_id = '';
ALTER TABLE slabs MODIFY COLUMN client_id VARCHAR(36) NOT NULL;
ALTER TABLE slabs ADD INDEX ix_slabs_client_id (client_id);
ALTER TABLE slabs ADD CONSTRAINT uq_slab_floor_client UNIQUE (floor_id, client_id);
