--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE jscaux;
ALTER ROLE jscaux WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION;
CREATE ROLE scipostv1db;
ALTER ROLE scipostv1db WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION PASSWORD 'md5f9ad7df4d8be546aef4080742bb26d2f';






--
-- Database creation
--

CREATE DATABASE jscaux WITH TEMPLATE = template0 OWNER = jscaux;
CREATE DATABASE scipostv1db WITH TEMPLATE = template0 OWNER = jscaux;
REVOKE ALL ON DATABASE scipostv1db FROM PUBLIC;
REVOKE ALL ON DATABASE scipostv1db FROM jscaux;
GRANT ALL ON DATABASE scipostv1db TO jscaux;
GRANT CONNECT,TEMPORARY ON DATABASE scipostv1db TO PUBLIC;
REVOKE ALL ON DATABASE template1 FROM PUBLIC;
REVOKE ALL ON DATABASE template1 FROM jscaux;
GRANT ALL ON DATABASE template1 TO jscaux;
GRANT CONNECT ON DATABASE template1 TO PUBLIC;


\connect jscaux

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: public; Type: ACL; Schema: -; Owner: jscaux
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM jscaux;
GRANT ALL ON SCHEMA public TO jscaux;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\connect postgres

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: postgres; Type: COMMENT; Schema: -; Owner: jscaux
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: public; Type: ACL; Schema: -; Owner: jscaux
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM jscaux;
GRANT ALL ON SCHEMA public TO jscaux;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\connect scipostv1db

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


ALTER TABLE auth_group OWNER TO scipostv1db;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_group_id_seq OWNER TO scipostv1db;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_group_id_seq OWNED BY auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE auth_group_permissions OWNER TO scipostv1db;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_group_permissions_id_seq OWNER TO scipostv1db;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_group_permissions_id_seq OWNED BY auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE auth_permission OWNER TO scipostv1db;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_permission_id_seq OWNER TO scipostv1db;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_permission_id_seq OWNED BY auth_permission.id;


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(30) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE auth_user OWNER TO scipostv1db;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE auth_user_groups OWNER TO scipostv1db;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_user_groups_id_seq OWNER TO scipostv1db;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_user_groups_id_seq OWNED BY auth_user_groups.id;


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_user_id_seq OWNER TO scipostv1db;

--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_user_id_seq OWNED BY auth_user.id;


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE auth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE auth_user_user_permissions OWNER TO scipostv1db;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_user_user_permissions_id_seq OWNER TO scipostv1db;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE auth_user_user_permissions_id_seq OWNED BY auth_user_user_permissions.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE django_admin_log OWNER TO scipostv1db;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE django_admin_log_id_seq OWNER TO scipostv1db;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE django_content_type OWNER TO scipostv1db;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE django_content_type_id_seq OWNER TO scipostv1db;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE django_migrations OWNER TO scipostv1db;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE django_migrations_id_seq OWNER TO scipostv1db;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE django_session OWNER TO scipostv1db;

--
-- Name: scipost_authorreply; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_authorreply (
    id integer NOT NULL,
    status smallint NOT NULL,
    reply_text text NOT NULL,
    date_submitted timestamp with time zone NOT NULL,
    nr_ratings integer NOT NULL,
    clarity_rating numeric(3,0) NOT NULL,
    correctness_rating numeric(3,0) NOT NULL,
    usefulness_rating numeric(3,0) NOT NULL,
    author_id integer NOT NULL,
    in_reply_to_comment_id integer,
    in_reply_to_report_id integer,
    commentary_id integer,
    submission_id integer
);


ALTER TABLE scipost_authorreply OWNER TO scipostv1db;

--
-- Name: scipost_authorreply_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_authorreply_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_authorreply_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_authorreply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_authorreply_id_seq OWNED BY scipost_authorreply.id;


--
-- Name: scipost_authorreplyrating; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_authorreplyrating (
    id integer NOT NULL,
    clarity smallint NOT NULL,
    correctness smallint NOT NULL,
    usefulness smallint NOT NULL,
    rater_id integer NOT NULL,
    reply_id integer NOT NULL,
    CONSTRAINT scipost_authorreplyrating_clarity_check CHECK ((clarity >= 0)),
    CONSTRAINT scipost_authorreplyrating_correctness_check CHECK ((correctness >= 0)),
    CONSTRAINT scipost_authorreplyrating_usefulness_check CHECK ((usefulness >= 0))
);


ALTER TABLE scipost_authorreplyrating OWNER TO scipostv1db;

--
-- Name: scipost_authorreplyrating_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_authorreplyrating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_authorreplyrating_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_authorreplyrating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_authorreplyrating_id_seq OWNED BY scipost_authorreplyrating.id;


--
-- Name: scipost_comment; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_comment (
    id integer NOT NULL,
    status smallint NOT NULL,
    comment_text text NOT NULL,
    date_submitted timestamp with time zone NOT NULL,
    nr_ratings integer NOT NULL,
    clarity_rating numeric(3,0) NOT NULL,
    correctness_rating numeric(3,0) NOT NULL,
    usefulness_rating numeric(3,0) NOT NULL,
    author_id integer NOT NULL,
    commentary_id integer,
    in_reply_to_id integer,
    submission_id integer
);


ALTER TABLE scipost_comment OWNER TO scipostv1db;

--
-- Name: scipost_comment_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_comment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_comment_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_comment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_comment_id_seq OWNED BY scipost_comment.id;


--
-- Name: scipost_commentary; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_commentary (
    id integer NOT NULL,
    vetted boolean NOT NULL,
    type character varying(9) NOT NULL,
    open_for_commenting boolean NOT NULL,
    pub_title character varying(300) NOT NULL,
    arxiv_link character varying(200) NOT NULL,
    "pub_DOI_link" character varying(200) NOT NULL,
    author_list character varying(1000) NOT NULL,
    pub_date date NOT NULL,
    pub_abstract text NOT NULL,
    nr_ratings integer NOT NULL,
    clarity_rating numeric(3,0) NOT NULL,
    correctness_rating numeric(3,0) NOT NULL,
    usefulness_rating numeric(3,0) NOT NULL,
    latest_activity timestamp with time zone NOT NULL,
    vetted_by_id integer
);


ALTER TABLE scipost_commentary OWNER TO scipostv1db;

--
-- Name: scipost_commentary_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_commentary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_commentary_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_commentary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_commentary_id_seq OWNED BY scipost_commentary.id;


--
-- Name: scipost_commentaryrating; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_commentaryrating (
    id integer NOT NULL,
    clarity smallint NOT NULL,
    correctness smallint NOT NULL,
    usefulness smallint NOT NULL,
    commentary_id integer NOT NULL,
    rater_id integer NOT NULL,
    CONSTRAINT scipost_commentaryrating_clarity_check CHECK ((clarity >= 0)),
    CONSTRAINT scipost_commentaryrating_correctness_check CHECK ((correctness >= 0)),
    CONSTRAINT scipost_commentaryrating_usefulness_check CHECK ((usefulness >= 0))
);


ALTER TABLE scipost_commentaryrating OWNER TO scipostv1db;

--
-- Name: scipost_commentaryrating_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_commentaryrating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_commentaryrating_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_commentaryrating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_commentaryrating_id_seq OWNED BY scipost_commentaryrating.id;


--
-- Name: scipost_commentrating; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_commentrating (
    id integer NOT NULL,
    clarity smallint NOT NULL,
    correctness smallint NOT NULL,
    usefulness smallint NOT NULL,
    comment_id integer NOT NULL,
    rater_id integer NOT NULL,
    CONSTRAINT scipost_commentrating_clarity_check CHECK ((clarity >= 0)),
    CONSTRAINT scipost_commentrating_correctness_check CHECK ((correctness >= 0)),
    CONSTRAINT scipost_commentrating_usefulness_check CHECK ((usefulness >= 0))
);


ALTER TABLE scipost_commentrating OWNER TO scipostv1db;

--
-- Name: scipost_commentrating_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_commentrating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_commentrating_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_commentrating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_commentrating_id_seq OWNED BY scipost_commentrating.id;


--
-- Name: scipost_contributor; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_contributor (
    id integer NOT NULL,
    rank smallint NOT NULL,
    title character varying(4) NOT NULL,
    affiliation character varying(300) NOT NULL,
    address character varying(1000) NOT NULL,
    personalwebpage character varying(200) NOT NULL,
    nr_reports smallint NOT NULL,
    report_clarity_rating numeric(3,0) NOT NULL,
    report_correctness_rating numeric(3,0) NOT NULL,
    report_usefulness_rating numeric(3,0) NOT NULL,
    nr_comments smallint NOT NULL,
    comment_clarity_rating numeric(3,0) NOT NULL,
    comment_correctness_rating numeric(3,0) NOT NULL,
    comment_usefulness_rating numeric(3,0) NOT NULL,
    user_id integer NOT NULL,
    orcid_id character varying(20),
    CONSTRAINT scipost_contributor_nr_comments_check CHECK ((nr_comments >= 0)),
    CONSTRAINT scipost_contributor_nr_reports_check CHECK ((nr_reports >= 0))
);


ALTER TABLE scipost_contributor OWNER TO scipostv1db;

--
-- Name: scipost_contributor_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_contributor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_contributor_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_contributor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_contributor_id_seq OWNED BY scipost_contributor.id;


--
-- Name: scipost_report; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_report (
    id integer NOT NULL,
    status smallint NOT NULL,
    strengths text NOT NULL,
    weaknesses text NOT NULL,
    report text NOT NULL,
    requested_changes text NOT NULL,
    recommendation smallint NOT NULL,
    date_invited timestamp with time zone,
    date_submitted timestamp with time zone NOT NULL,
    nr_ratings integer NOT NULL,
    clarity_rating numeric(3,0) NOT NULL,
    correctness_rating numeric(3,0) NOT NULL,
    usefulness_rating numeric(3,0) NOT NULL,
    author_id integer NOT NULL,
    invited_by_id integer,
    submission_id integer NOT NULL
);


ALTER TABLE scipost_report OWNER TO scipostv1db;

--
-- Name: scipost_report_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_report_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_report_id_seq OWNED BY scipost_report.id;


--
-- Name: scipost_reportrating; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_reportrating (
    id integer NOT NULL,
    clarity smallint NOT NULL,
    correctness smallint NOT NULL,
    usefulness smallint NOT NULL,
    rater_id integer NOT NULL,
    report_id integer NOT NULL,
    CONSTRAINT scipost_reportrating_clarity_check CHECK ((clarity >= 0)),
    CONSTRAINT scipost_reportrating_correctness_check CHECK ((correctness >= 0)),
    CONSTRAINT scipost_reportrating_usefulness_check CHECK ((usefulness >= 0))
);


ALTER TABLE scipost_reportrating OWNER TO scipostv1db;

--
-- Name: scipost_reportrating_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_reportrating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_reportrating_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_reportrating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_reportrating_id_seq OWNED BY scipost_reportrating.id;


--
-- Name: scipost_submission; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_submission (
    id integer NOT NULL,
    vetted boolean NOT NULL,
    submitted_to_journal character varying(30) NOT NULL,
    status smallint NOT NULL,
    open_for_reporting boolean NOT NULL,
    open_for_commenting boolean NOT NULL,
    title character varying(300) NOT NULL,
    author_list character varying(1000) NOT NULL,
    abstract text NOT NULL,
    arxiv_link character varying(200) NOT NULL,
    submission_date date NOT NULL,
    nr_ratings integer NOT NULL,
    clarity_rating numeric(3,0) NOT NULL,
    correctness_rating numeric(3,0) NOT NULL,
    usefulness_rating numeric(3,0) NOT NULL,
    latest_activity timestamp with time zone NOT NULL,
    editor_in_charge_id integer,
    submitted_by_id integer NOT NULL,
    specialization character varying(1) NOT NULL
);


ALTER TABLE scipost_submission OWNER TO scipostv1db;

--
-- Name: scipost_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_submission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_submission_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_submission_id_seq OWNED BY scipost_submission.id;


--
-- Name: scipost_submissionrating; Type: TABLE; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE TABLE scipost_submissionrating (
    id integer NOT NULL,
    clarity smallint NOT NULL,
    correctness smallint NOT NULL,
    usefulness smallint NOT NULL,
    rater_id integer NOT NULL,
    submission_id integer NOT NULL,
    CONSTRAINT scipost_submissionrating_clarity_check CHECK ((clarity >= 0)),
    CONSTRAINT scipost_submissionrating_correctness_check CHECK ((correctness >= 0)),
    CONSTRAINT scipost_submissionrating_usefulness_check CHECK ((usefulness >= 0))
);


ALTER TABLE scipost_submissionrating OWNER TO scipostv1db;

--
-- Name: scipost_submissionrating_id_seq; Type: SEQUENCE; Schema: public; Owner: scipostv1db
--

CREATE SEQUENCE scipost_submissionrating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scipost_submissionrating_id_seq OWNER TO scipostv1db;

--
-- Name: scipost_submissionrating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scipostv1db
--

ALTER SEQUENCE scipost_submissionrating_id_seq OWNED BY scipost_submissionrating.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_groups ALTER COLUMN id SET DEFAULT nextval('auth_user_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('auth_user_user_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply ALTER COLUMN id SET DEFAULT nextval('scipost_authorreply_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreplyrating ALTER COLUMN id SET DEFAULT nextval('scipost_authorreplyrating_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment ALTER COLUMN id SET DEFAULT nextval('scipost_comment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentary ALTER COLUMN id SET DEFAULT nextval('scipost_commentary_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentaryrating ALTER COLUMN id SET DEFAULT nextval('scipost_commentaryrating_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentrating ALTER COLUMN id SET DEFAULT nextval('scipost_commentrating_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_contributor ALTER COLUMN id SET DEFAULT nextval('scipost_contributor_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report ALTER COLUMN id SET DEFAULT nextval('scipost_report_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_reportrating ALTER COLUMN id SET DEFAULT nextval('scipost_reportrating_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submission ALTER COLUMN id SET DEFAULT nextval('scipost_submission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submissionrating ALTER COLUMN id SET DEFAULT nextval('scipost_submissionrating_id_seq'::regclass);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_group (id, name) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_group_id_seq', 1, false);


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 1, false);


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can add permission	2	add_permission
5	Can change permission	2	change_permission
6	Can delete permission	2	delete_permission
7	Can add group	3	add_group
8	Can change group	3	change_group
9	Can delete group	3	delete_group
10	Can add user	4	add_user
11	Can change user	4	change_user
12	Can delete user	4	delete_user
13	Can add content type	5	add_contenttype
14	Can change content type	5	change_contenttype
15	Can delete content type	5	delete_contenttype
16	Can add session	6	add_session
17	Can change session	6	change_session
18	Can delete session	6	delete_session
19	Can add contributor	7	add_contributor
20	Can change contributor	7	change_contributor
21	Can delete contributor	7	delete_contributor
22	Can add commentary	8	add_commentary
23	Can change commentary	8	change_commentary
24	Can delete commentary	8	delete_commentary
25	Can add commentary rating	9	add_commentaryrating
26	Can change commentary rating	9	change_commentaryrating
27	Can delete commentary rating	9	delete_commentaryrating
28	Can add submission	10	add_submission
29	Can change submission	10	change_submission
30	Can delete submission	10	delete_submission
31	Can add submission rating	11	add_submissionrating
32	Can change submission rating	11	change_submissionrating
33	Can delete submission rating	11	delete_submissionrating
34	Can add report	12	add_report
35	Can change report	12	change_report
36	Can delete report	12	delete_report
37	Can add report rating	13	add_reportrating
38	Can change report rating	13	change_reportrating
39	Can delete report rating	13	delete_reportrating
40	Can add comment	14	add_comment
41	Can change comment	14	change_comment
42	Can delete comment	14	delete_comment
43	Can add comment rating	15	add_commentrating
44	Can change comment rating	15	change_commentrating
45	Can delete comment rating	15	delete_commentrating
46	Can add author reply	16	add_authorreply
47	Can change author reply	16	change_authorreply
48	Can delete author reply	16	delete_authorreply
49	Can add author reply rating	17	add_authorreplyrating
50	Can change author reply rating	17	change_authorreplyrating
51	Can delete author reply rating	17	delete_authorreplyrating
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_permission_id_seq', 51, true);


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$20000$sAETRHYQd7fU$y0Ot0wtu+RW1H1iUCMsDo+RoPBbzaz9v6A1n2LWvIyE=	2015-11-18 22:17:00.533193+01	t	jscaux			J.S.Caux@uva.nl	t	t	2015-11-18 22:16:53.171895+01
3	pbkdf2_sha256$20000$kTJBJZ9VjNw1$02BAiUoy1S3+MlHSGUQzLZ/PHIg2Z2dnahGflzlOwMc=	2015-11-20 00:31:52.337212+01	f	opera	opera	opera	opera@opera.com	f	t	2015-11-20 00:26:22.258153+01
2	pbkdf2_sha256$20000$ZnS9xtrZUd4a$ZJthVdlNh+xcsw7elxFZ0DE25kydLNaIN5BM9XrY7Ig=	2015-11-23 21:14:17.957696+01	f	test1	test1	test1	test1@test1.com	f	t	2015-11-18 22:20:04.973505+01
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_user_id_seq', 3, true);


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('auth_user_user_permissions_id_seq', 1, false);


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2015-11-18 22:20:18.451613+01	1	test1	2	Changed rank.	7	1
2	2015-11-18 22:32:02.420275+01	2	I like it.	3		14	1
3	2015-11-19 00:12:09.832434+01	1	The author likes that you like it.	2	Changed commentary.	16	1
4	2015-11-19 00:46:29.063346+01	2	This is an empty report.	2	Changed submission.	16	1
5	2015-11-19 14:51:10.252985+01	1	Paper1	2	Changed submitted_to_journal.	10	1
6	2015-11-21 01:01:58.091172+01	1	Paper1	2	Changed vetted.	10	1
7	2015-11-21 01:02:12.227195+01	2	Paper2	2	Changed vetted and submitted_to_journal.	10	1
8	2015-11-21 01:02:21.641089+01	3	submit2	2	Changed vetted.	10	1
9	2015-11-23 00:54:50.907456+01	3	submit2	2	Changed status.	10	1
10	2015-11-23 00:55:15.293597+01	3	submit2	2	Changed vetted.	10	1
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 10, true);


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	scipost	contributor
8	scipost	commentary
9	scipost	commentaryrating
10	scipost	submission
11	scipost	submissionrating
12	scipost	report
13	scipost	reportrating
14	scipost	comment
15	scipost	commentrating
16	scipost	authorreply
17	scipost	authorreplyrating
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('django_content_type_id_seq', 17, true);


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2015-11-18 22:16:23.523294+01
2	auth	0001_initial	2015-11-18 22:16:23.603751+01
3	admin	0001_initial	2015-11-18 22:16:23.630469+01
4	contenttypes	0002_remove_content_type_name	2015-11-18 22:16:23.675043+01
5	auth	0002_alter_permission_name_max_length	2015-11-18 22:16:23.68842+01
6	auth	0003_alter_user_email_max_length	2015-11-18 22:16:23.703624+01
7	auth	0004_alter_user_username_opts	2015-11-18 22:16:23.71699+01
8	auth	0005_alter_user_last_login_null	2015-11-18 22:16:23.73192+01
9	auth	0006_require_contenttypes_0002	2015-11-18 22:16:23.734427+01
10	scipost	0001_initial	2015-11-18 22:16:24.187552+01
11	sessions	0001_initial	2015-11-18 22:16:24.201602+01
12	scipost	0002_authorreply_authorreplyrating	2015-11-18 23:45:07.861184+01
13	scipost	0003_auto_20151119_0007	2015-11-19 00:07:06.169289+01
14	scipost	0004_contributor_orcid_id	2015-11-19 14:23:05.078701+01
15	scipost	0005_auto_20151119_1447	2015-11-19 14:47:19.344569+01
16	scipost	0006_auto_20151119_1450	2015-11-19 14:50:53.812637+01
17	scipost	0007_auto_20151120_0027	2015-11-20 00:27:10.905975+01
18	scipost	0008_auto_20151120_0047	2015-11-20 00:47:48.545058+01
19	scipost	0009_auto_20151120_0232	2015-11-20 02:32:54.223973+01
20	scipost	0010_remove_submission_specialization	2015-11-20 02:35:44.039159+01
21	scipost	0011_auto_20151120_0237	2015-11-20 02:37:38.709307+01
22	scipost	0012_auto_20151120_0257	2015-11-20 02:57:59.495901+01
23	scipost	0013_auto_20151120_0258	2015-11-20 02:58:12.333203+01
24	scipost	0014_auto_20151120_0306	2015-11-20 03:06:31.202053+01
25	scipost	0015_auto_20151121_1257	2015-11-21 12:57:13.203201+01
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('django_migrations_id_seq', 25, true);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
zomjmwcrpqfs8f0ymlarn7le5rm4x52o	ZTAxMDRhMGFmYjRlZmJiYTc2OGUwODljMmI3NTc5N2I4NjhkOTI1Njp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9oYXNoIjoiNzI3OWJiNDlhMDY0YWRkY2FhYWU0NGZlMjQzMjk1ZDBhYWViZjk1YSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-02 22:17:00.535068+01
znwofoutntdeeu9o9kj3ts7kyiegel36	NTBkNTFkM2I5Y2U0NTYzZGUxOTRhYzNiMGE4NDQ2NTJlMDRjNTA0MTp7ImNvbW1lbnRhcnlfaWQiOiIyIiwiX2F1dGhfdXNlcl9oYXNoIjoiYzk3MmFiN2RiYTkwOWY0MWZmNzlhZjEwOWJmOTNkODVlY2E0YWM0MyIsInN1Ym1pc3Npb25faWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2lkIjoiMyJ9	2015-12-05 12:59:56.883217+01
rbi9iratet8n1d5z1ob4xnvszsbx359u	YTcwMGE1N2NkYjUwNWE4Y2FhYmI3ZDkxNWRmN2IxZDc5N2NiOGRiZjp7Il9hdXRoX3VzZXJfaWQiOiIyIiwiX2F1dGhfdXNlcl9oYXNoIjoiYWY0NTk2OGQ4N2QzNTA3NzgwYWE2NGUxNGJjZTMzOWFjYzcxNGNhYyIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-07 21:14:17.972148+01
\.


--
-- Data for Name: scipost_authorreply; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_authorreply (id, status, reply_text, date_submitted, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, author_id, in_reply_to_comment_id, in_reply_to_report_id, commentary_id, submission_id) FROM stdin;
1	1	The author likes that you like it.	2015-11-18 23:45:11+01	0	0	0	0	1	1	\N	1	\N
2	1	This is an empty report.	2015-11-19 00:36:26+01	0	0	0	0	1	\N	1	\N	1
3	1	What a useful comment for the authors.	2015-11-19 00:47:53.331291+01	0	0	0	0	1	4	\N	\N	1
4	1	We indeed like it very much.	2015-11-19 02:23:25.052279+01	0	0	0	0	1	1	\N	1	\N
5	1	We await your second comment.	2015-11-19 02:27:05.752186+01	0	0	0	0	1	4	\N	\N	1
6	1	Thanks for liking it.	2015-11-21 12:59:25.784166+01	0	0	0	0	2	3	\N	1	\N
7	0	Thanks	2015-11-24 09:30:34.707145+01	0	0	0	0	1	6	\N	2	\N
\.


--
-- Name: scipost_authorreply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_authorreply_id_seq', 7, true);


--
-- Data for Name: scipost_authorreplyrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_authorreplyrating (id, clarity, correctness, usefulness, rater_id, reply_id) FROM stdin;
\.


--
-- Name: scipost_authorreplyrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_authorreplyrating_id_seq', 1, false);


--
-- Data for Name: scipost_comment; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_comment (id, status, comment_text, date_submitted, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, author_id, commentary_id, in_reply_to_id, submission_id) FROM stdin;
1	1	I like it.	2015-11-18 22:31:05.057914+01	0	0	0	0	1	1	\N	\N
3	1	Another contributor likes it.	2015-11-19 00:18:52.336946+01	0	0	0	0	1	1	1	\N
4	1	First comment.	2015-11-19 00:46:52.07598+01	0	0	0	0	1	\N	\N	1
5	1	Yeah, let's see your second comment.	2015-11-19 02:31:50.429428+01	0	0	0	0	1	\N	4	1
7	1	What an uninteresting paper who would even read this??????	2015-11-23 20:22:40.659499+01	0	0	0	0	1	2	\N	\N
6	1	This is a great paper.	2015-11-21 12:55:19.73328+01	1	10	0	0	2	2	\N	\N
\.


--
-- Name: scipost_comment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_comment_id_seq', 7, true);


--
-- Data for Name: scipost_commentary; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentary (id, vetted, type, open_for_commenting, pub_title, arxiv_link, "pub_DOI_link", author_list, pub_date, pub_abstract, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, latest_activity, vetted_by_id) FROM stdin;
2	t	published	t	Complete Generalized Gibbs Ensemble in an interacting Theory	http://arxiv.org/abs/1507.02993v2	http://dx.doi.org/10.1103/PhysRevLett.115.157201	Enej Ilievski, Jacopo De Nardis, Bram Wouters, Jean-Sebastien Caux, Fabian H. L. Essler, Tomaz Prosen	2015-07-10	In integrable many-particle systems, it is widely believed that the stationary state reached at late times after a quantum quench can be described by a generalized Gibbs ensemble (GGE) constructed from their extensive number of conserved charges. A crucial issue is then to identify a complete set of these charges, enabling the GGE to provide exact steady state predictions. Here we solve this long-standing problem for the case of the spin-1/2 Heisenberg chain by explicitly constructing a GGE which uniquely fixes the macrostate describing the stationary behaviour after a general quantum quench. A crucial ingredient in our method, which readily generalizes to other integrable models, are recently discovered quasi-local charges. As a test, we reproduce the exact post-quench steady state of the Neel quench problem obtained previously by means of the Quench Action method.	0	0	0	0	2015-11-19 13:05:55.381085+01	\N
1	t	preprint	t	Reunion probabilities of N one-dimensional random walkers with mixed boundary conditions	http://arxiv.org/abs/1311.0654v1		Isaac Pérez Castillo, Thomas Dupic	2013-04-11	In this work we extend the results of the reunion probability of $N$ one-dimensional random walkers to include mixed boundary conditions between their trajectories. The level of the mixture is controlled by a parameter $c$, which can be varied from $c=0$ (independent walkers) to $c\\to\\infty$ (vicious walkers). The expressions are derived by using Quantum Mechanics formalism (QMf) which allows us to map this problem into a Lieb-Liniger gas (LLg) of $N$ one-dimensional particles. We use Bethe ansatz and Gaudin's conjecture to obtain the normalized wave-functions and use this information to construct the propagator. As it is well-known, depending on the boundary conditions imposed at the endpoints of a line segment, the statistics of the maximum heights of the reunited trajectories have some connections with different ensembles in Random Matrix Theory (RMT). Here we seek to extend those results and consider four models: absorbing, periodic, reflecting, and mixed. In all four cases, the probability that the maximum height is less or equal than $L$ takes the form $F_N(L)=A_N\\sum_{k\\in\\Omega_{B}}\\int Dz e^{-\\sum_{j=1}^Nk_j^2+G_N(k)-\\sum_{j,\\ell=1}^N z_jV_{j\\ell}(k)\\overline{z}_\\ell}$, where $A_N$ is a normalization constant, $G_N(k)$ and $V_{j\\ell}(k)$ depend on the type of boundary condition, and $\\Omega_{B}$ is the solution set of quasi-momenta $k$ obeying the Bethe equations for that particular boundary condition.	1	90	100	100	2015-11-18 22:22:22.507372+01	\N
3	t	published	t	Probing the Excitations of a Lieb-Liniger Gas from Weak to Strong Coupling	http://arxiv.org/abs/1505.08152	http://dx.doi.org/10.1103/PhysRevLett.115.085301	Florian Meinert, Milosz Panfil, Manfred J. Mark, Katharina Lauber, Jean-Sébastien Caux, Hanns-Christoph Nägerl	2015-08-15	We probe the excitation spectrum of an ultracold one-dimensional Bose gas of Cesium atoms with repulsive contact interaction that we tune from the weakly to the strongly interacting regime via a magnetic Feshbach resonance. The dynamical structure factor, experimentally obtained using Bragg spectroscopy, is compared to integrability-based calculations valid at arbitrary interactions and finite temperatures. Our results unequivocally underly the fact that hole-like excitations, which have no counterpart in higher dimensions, actively shape the dynamical response of the gas.	0	0	0	0	2015-11-21 12:50:11.999992+01	\N
\.


--
-- Name: scipost_commentary_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentary_id_seq', 3, true);


--
-- Data for Name: scipost_commentaryrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentaryrating (id, clarity, correctness, usefulness, commentary_id, rater_id) FROM stdin;
1	90	100	100	1	1
\.


--
-- Name: scipost_commentaryrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentaryrating_id_seq', 1, true);


--
-- Data for Name: scipost_commentrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentrating (id, clarity, correctness, usefulness, comment_id, rater_id) FROM stdin;
1	10	0	0	6	1
\.


--
-- Name: scipost_commentrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentrating_id_seq', 1, true);


--
-- Data for Name: scipost_contributor; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_contributor (id, rank, title, affiliation, address, personalwebpage, nr_reports, report_clarity_rating, report_correctness_rating, report_usefulness_rating, nr_comments, comment_clarity_rating, comment_correctness_rating, comment_usefulness_rating, user_id, orcid_id) FROM stdin;
1	4	PR	test1			1	0	0	0	5	0	0	0	2	
2	1	PR	opera	opera		1	0	0	0	1	10	0	0	3	
\.


--
-- Name: scipost_contributor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_contributor_id_seq', 2, true);


--
-- Data for Name: scipost_report; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_report (id, status, strengths, weaknesses, report, requested_changes, recommendation, date_invited, date_submitted, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, author_id, invited_by_id, submission_id) FROM stdin;
1	1	Strong.	Weak.	Readable.	Rewrite.	1	\N	2015-11-18 22:41:30.836513+01	0	0	0	0	1	\N	1
2	1	Hey	Ho	Tiddly	Bum	1	\N	2015-11-21 12:59:56.875594+01	0	0	0	0	2	\N	1
\.


--
-- Name: scipost_report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_report_id_seq', 2, true);


--
-- Data for Name: scipost_reportrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_reportrating (id, clarity, correctness, usefulness, rater_id, report_id) FROM stdin;
\.


--
-- Name: scipost_reportrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_reportrating_id_seq', 1, false);


--
-- Data for Name: scipost_submission; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_submission (id, vetted, submitted_to_journal, status, open_for_reporting, open_for_commenting, title, author_list, abstract, arxiv_link, submission_date, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, latest_activity, editor_in_charge_id, submitted_by_id, specialization) FROM stdin;
1	t	SciPost Physics Letters	1	t	t	Paper1	Author1	Abstract1	http://arxiv.org/paper1	2015-11-18	1	70	50	30	2015-11-18 22:39:46+01	1	1	A
2	t	SciPost Physics X	1	t	t	Paper2	Auth2	Abs2	http://arxiv.org/1511.9999v1	2015-11-19	0	0	0	0	2015-11-19 15:08:59+01	1	1	A
3	t	SciPost Physics Letters	1	t	t	submit2	auth2	abs2	http://arxiv.org/paper2.com	2015-11-20	0	0	0	0	2015-11-20 00:49:44+01	1	2	A
4	t	SciPost Physics X	1	t	t	Some Weird Stuff	Maxim Caux	This is a very weird text that no one wrote	http://arxiv.org/maxv1	2015-11-23	0	0	0	0	2015-11-23 20:17:55.690899+01	1	1	G
\.


--
-- Name: scipost_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_submission_id_seq', 4, true);


--
-- Data for Name: scipost_submissionrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_submissionrating (id, clarity, correctness, usefulness, rater_id, submission_id) FROM stdin;
1	70	50	30	1	1
\.


--
-- Name: scipost_submissionrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_submissionrating_id_seq', 1, true);


--
-- Name: auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission_content_type_id_codename_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename);


--
-- Name: auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type_app_label_7d32226aaf54ec25_uniq; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_7d32226aaf54ec25_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: scipost_authorreply_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_authorreply_pkey PRIMARY KEY (id);


--
-- Name: scipost_authorreplyrating_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_authorreplyrating
    ADD CONSTRAINT scipost_authorreplyrating_pkey PRIMARY KEY (id);


--
-- Name: scipost_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_comment_pkey PRIMARY KEY (id);


--
-- Name: scipost_commentary_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_commentary
    ADD CONSTRAINT scipost_commentary_pkey PRIMARY KEY (id);


--
-- Name: scipost_commentaryrating_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_commentaryrating
    ADD CONSTRAINT scipost_commentaryrating_pkey PRIMARY KEY (id);


--
-- Name: scipost_commentrating_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_commentrating
    ADD CONSTRAINT scipost_commentrating_pkey PRIMARY KEY (id);


--
-- Name: scipost_contributor_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_contributor
    ADD CONSTRAINT scipost_contributor_pkey PRIMARY KEY (id);


--
-- Name: scipost_contributor_user_id_key; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_contributor
    ADD CONSTRAINT scipost_contributor_user_id_key UNIQUE (user_id);


--
-- Name: scipost_report_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_report_pkey PRIMARY KEY (id);


--
-- Name: scipost_reportrating_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_reportrating
    ADD CONSTRAINT scipost_reportrating_pkey PRIMARY KEY (id);


--
-- Name: scipost_submission_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_submission
    ADD CONSTRAINT scipost_submission_pkey PRIMARY KEY (id);


--
-- Name: scipost_submissionrating_pkey; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY scipost_submissionrating
    ADD CONSTRAINT scipost_submissionrating_pkey PRIMARY KEY (id);


--
-- Name: auth_group_name_243fb6146d665317_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_group_name_243fb6146d665317_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_0e939a4f; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_group_permissions_0e939a4f ON auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_8373b171; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_group_permissions_8373b171 ON auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_417f1b1c; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_permission_417f1b1c ON auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_0e939a4f; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_groups_0e939a4f ON auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_e8701ad4; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_groups_e8701ad4 ON auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_8373b171; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_user_permissions_8373b171 ON auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_e8701ad4; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_user_permissions_e8701ad4 ON auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_12b13d01a12d892a_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_username_12b13d01a12d892a_like ON auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_417f1b1c; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX django_admin_log_417f1b1c ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_e8701ad4; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX django_admin_log_e8701ad4 ON django_admin_log USING btree (user_id);


--
-- Name: django_session_de54fa62; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX django_session_de54fa62 ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_3207e98caaef7623_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX django_session_session_key_3207e98caaef7623_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: scipost_authorreply_1dd9cfcc; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreply_1dd9cfcc ON scipost_authorreply USING btree (submission_id);


--
-- Name: scipost_authorreply_4f331e2f; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreply_4f331e2f ON scipost_authorreply USING btree (author_id);


--
-- Name: scipost_authorreply_c229db37; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreply_c229db37 ON scipost_authorreply USING btree (commentary_id);


--
-- Name: scipost_authorreply_daece9cb; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreply_daece9cb ON scipost_authorreply USING btree (in_reply_to_report_id);


--
-- Name: scipost_authorreply_f72f5890; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreply_f72f5890 ON scipost_authorreply USING btree (in_reply_to_comment_id);


--
-- Name: scipost_authorreplyrating_9e4fc8b5; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreplyrating_9e4fc8b5 ON scipost_authorreplyrating USING btree (rater_id);


--
-- Name: scipost_authorreplyrating_bbc2f847; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_authorreplyrating_bbc2f847 ON scipost_authorreplyrating USING btree (reply_id);


--
-- Name: scipost_comment_1dd9cfcc; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_comment_1dd9cfcc ON scipost_comment USING btree (submission_id);


--
-- Name: scipost_comment_48c25820; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_comment_48c25820 ON scipost_comment USING btree (in_reply_to_id);


--
-- Name: scipost_comment_4f331e2f; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_comment_4f331e2f ON scipost_comment USING btree (author_id);


--
-- Name: scipost_comment_c229db37; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_comment_c229db37 ON scipost_comment USING btree (commentary_id);


--
-- Name: scipost_commentary_47ed100c; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_commentary_47ed100c ON scipost_commentary USING btree (vetted_by_id);


--
-- Name: scipost_commentaryrating_9e4fc8b5; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_commentaryrating_9e4fc8b5 ON scipost_commentaryrating USING btree (rater_id);


--
-- Name: scipost_commentaryrating_c229db37; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_commentaryrating_c229db37 ON scipost_commentaryrating USING btree (commentary_id);


--
-- Name: scipost_commentrating_69b97d17; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_commentrating_69b97d17 ON scipost_commentrating USING btree (comment_id);


--
-- Name: scipost_commentrating_9e4fc8b5; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_commentrating_9e4fc8b5 ON scipost_commentrating USING btree (rater_id);


--
-- Name: scipost_report_1dd9cfcc; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_report_1dd9cfcc ON scipost_report USING btree (submission_id);


--
-- Name: scipost_report_36fc3d93; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_report_36fc3d93 ON scipost_report USING btree (invited_by_id);


--
-- Name: scipost_report_4f331e2f; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_report_4f331e2f ON scipost_report USING btree (author_id);


--
-- Name: scipost_reportrating_6f78b20c; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_reportrating_6f78b20c ON scipost_reportrating USING btree (report_id);


--
-- Name: scipost_reportrating_9e4fc8b5; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_reportrating_9e4fc8b5 ON scipost_reportrating USING btree (rater_id);


--
-- Name: scipost_submission_31174c9a; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_submission_31174c9a ON scipost_submission USING btree (submitted_by_id);


--
-- Name: scipost_submission_57927b23; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_submission_57927b23 ON scipost_submission USING btree (editor_in_charge_id);


--
-- Name: scipost_submissionrating_1dd9cfcc; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_submissionrating_1dd9cfcc ON scipost_submissionrating USING btree (submission_id);


--
-- Name: scipost_submissionrating_9e4fc8b5; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX scipost_submissionrating_9e4fc8b5 ON scipost_submissionrating USING btree (rater_id);


--
-- Name: auth_content_type_id_75e6ae31abbebaa1_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_content_type_id_75e6ae31abbebaa1_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissio_group_id_69b6a92c126620cb_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_group_id_69b6a92c126620cb_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permission_id_2af58f1bb854fe46_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permission_id_2af58f1bb854fe46_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups_group_id_39824aa73dda5bf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_39824aa73dda5bf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups_user_id_3a9940ca2e89ec5e_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_3a9940ca2e89ec5e_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_u_permission_id_10a7622450db5f0_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_u_permission_id_10a7622450db5f0_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permiss_user_id_220d186eb3650ce4_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permiss_user_id_220d186eb3650ce4_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: djan_content_type_id_38dfec5f7e30a719_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT djan_content_type_id_38dfec5f7e30a719_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_33c983bf8f6cef9d_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_33c983bf8f6cef9d_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: editor_in_charge_id_1eb081c7672a0361_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submission
    ADD CONSTRAINT editor_in_charge_id_1eb081c7672a0361_fk_scipost_contributor_id FOREIGN KEY (editor_in_charge_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: s_in_reply_to_comment_id_5526ba288d2cf230_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT s_in_reply_to_comment_id_5526ba288d2cf230_fk_scipost_comment_id FOREIGN KEY (in_reply_to_comment_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sci_in_reply_to_report_id_35020fceaf0ce21b_fk_scipost_report_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT sci_in_reply_to_report_id_35020fceaf0ce21b_fk_scipost_report_id FOREIGN KEY (in_reply_to_report_id) REFERENCES scipost_report(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scip_submitted_by_id_7bbfb6be40460915_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submission
    ADD CONSTRAINT scip_submitted_by_id_7bbfb6be40460915_fk_scipost_contributor_id FOREIGN KEY (submitted_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_au_author_id_657d535d36cde5fa_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_au_author_id_657d535d36cde5fa_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_aut_rater_id_3d6d1f3ad90a3373_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreplyrating
    ADD CONSTRAINT scipost_aut_rater_id_3d6d1f3ad90a3373_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_aut_reply_id_593ae18c455584a3_fk_scipost_authorreply_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreplyrating
    ADD CONSTRAINT scipost_aut_reply_id_593ae18c455584a3_fk_scipost_authorreply_id FOREIGN KEY (reply_id) REFERENCES scipost_authorreply(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_co_author_id_62ca0aa2e14d9fd6_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_co_author_id_62ca0aa2e14d9fd6_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_co_in_reply_to_id_75273a6da02eef7_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_co_in_reply_to_id_75273a6da02eef7_fk_scipost_comment_id FOREIGN KEY (in_reply_to_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_com_rater_id_60ba20d670ed92b7_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentaryrating
    ADD CONSTRAINT scipost_com_rater_id_60ba20d670ed92b7_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_com_rater_id_730aba9e953e3613_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentrating
    ADD CONSTRAINT scipost_com_rater_id_730aba9e953e3613_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_comme_comment_id_3b4c673c45c7c489_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentrating
    ADD CONSTRAINT scipost_comme_comment_id_3b4c673c45c7c489_fk_scipost_comment_id FOREIGN KEY (comment_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_102714de1fc19fd4_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentaryrating
    ADD CONSTRAINT scipost_commentary_id_102714de1fc19fd4_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_696b33666be9f0e3_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_commentary_id_696b33666be9f0e3_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_7ade0adc5b2cf289_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_commentary_id_7ade0adc5b2cf289_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_contributor_user_id_12351d0620355a18_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_contributor
    ADD CONSTRAINT scipost_contributor_user_id_12351d0620355a18_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_invited_by_id_2e66021a58f3780_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_invited_by_id_2e66021a58f3780_fk_scipost_contributor_id FOREIGN KEY (invited_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_re_author_id_73e385a0cc8767c1_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_re_author_id_73e385a0cc8767c1_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_rep_rater_id_7800cb5fe19f767c_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_reportrating
    ADD CONSTRAINT scipost_rep_rater_id_7800cb5fe19f767c_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_reportr_report_id_3ee2d0b9644132c4_fk_scipost_report_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_reportrating
    ADD CONSTRAINT scipost_reportr_report_id_3ee2d0b9644132c4_fk_scipost_report_id FOREIGN KEY (report_id) REFERENCES scipost_report(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_sub_rater_id_2bff2d3c7c72e9be_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submissionrating
    ADD CONSTRAINT scipost_sub_rater_id_2bff2d3c7c72e9be_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_182bea1067cb77fa_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_submission_id_182bea1067cb77fa_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_28020adff681e20e_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submissionrating
    ADD CONSTRAINT scipost_submission_id_28020adff681e20e_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_3a5af0a95f64c3df_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_submission_id_3a5af0a95f64c3df_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_5b3c14653298ba3c_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_submission_id_5b3c14653298ba3c_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_vetted_by_id_3e36f35ed29f72f7_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentary
    ADD CONSTRAINT scipost_vetted_by_id_3e36f35ed29f72f7_fk_scipost_contributor_id FOREIGN KEY (vetted_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: public; Type: ACL; Schema: -; Owner: jscaux
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM jscaux;
GRANT ALL ON SCHEMA public TO jscaux;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\connect template1

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: template1; Type: COMMENT; Schema: -; Owner: jscaux
--

COMMENT ON DATABASE template1 IS 'default template for new databases';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: public; Type: ACL; Schema: -; Owner: jscaux
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM jscaux;
GRANT ALL ON SCHEMA public TO jscaux;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database cluster dump complete
--

