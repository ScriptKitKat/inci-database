-- Domain enums. Preferred over CHECK constraints because they are
-- indexable, introspectable, and easy to extend with ALTER TYPE.

CREATE TYPE ingredient_rating AS ENUM ('superhero','great','average','not_good','bad');

CREATE TYPE irritancy_level AS ENUM ('low','medium','high');

CREATE TYPE alias_type AS ENUM (
  'inci','trade','common','iupac','synonym','typo','translation'
);

CREATE TYPE editorial_status AS ENUM ('draft','review','published','archived');

CREATE TYPE source_type AS ENUM (
  'cosing','pubchem','pubmed','open_beauty_facts','incidecoder','manual'
);
