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
    commentary_id integer,
    in_reply_to_comment_id integer,
    in_reply_to_report_id integer,
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
    orcid_id character varying(20),
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
    qualification smallint NOT NULL,
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
    submission_id integer NOT NULL,
    CONSTRAINT scipost_report_qualification_check CHECK ((qualification >= 0))
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
    domain character varying(1) NOT NULL,
    specialization character varying(1) NOT NULL,
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
    submitted_by_id integer NOT NULL
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
1	pbkdf2_sha256$20000$LDBGVXD440Se$bYbOPlWlxbp/hMJa+QJjfnS7MDJKduKksXm5kv2xHR0=	2015-11-28 17:27:03.013026+01	t	jscaux			J.S.Caux@uva.nl	t	t	2015-11-28 17:22:40.479645+01
2	pbkdf2_sha256$20000$c543GuXwlo5c$I2BMZVk6iEt3/8BaiMtL8YswmgWdIuTAiOMj3Q3/+sE=	2015-11-28 17:27:50.299663+01	f	test1	test1	test1	test1@test1.com	f	t	2015-11-28 17:24:22.148379+01
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

SELECT pg_catalog.setval('auth_user_id_seq', 2, true);


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
1	2015-11-28 17:27:15.205328+01	1	test1	2	Changed rank.	7	1
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 1, true);


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
1	contenttypes	0001_initial	2015-11-28 17:21:47.301639+01
2	auth	0001_initial	2015-11-28 17:21:47.381343+01
3	admin	0001_initial	2015-11-28 17:21:47.411744+01
4	contenttypes	0002_remove_content_type_name	2015-11-28 17:21:47.455104+01
5	auth	0002_alter_permission_name_max_length	2015-11-28 17:21:47.468536+01
6	auth	0003_alter_user_email_max_length	2015-11-28 17:21:47.482805+01
7	auth	0004_alter_user_username_opts	2015-11-28 17:21:47.49891+01
8	auth	0005_alter_user_last_login_null	2015-11-28 17:21:47.513072+01
9	auth	0006_require_contenttypes_0002	2015-11-28 17:21:47.514916+01
10	scipost	0001_initial	2015-11-28 17:21:48.377002+01
11	sessions	0001_initial	2015-11-28 17:21:48.391046+01
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('django_migrations_id_seq', 11, true);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
bqfpa7e4rz3zlq223nm2xkhvab9nnf9g	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:22:44.429354+01
ilq7lrdyz96qixjfk2pujuag6rzkdl1t	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:22:46.042299+01
kos0ovvi3y15iyxvplim6pj1j15l2f0m	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:22:54.787021+01
hfyfhl51dvvbp5bd1kq36d8umm7un5o2	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:23:27.202816+01
bllo7smxcsu39qaar1cyscuynozg3yir	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:24:30.85311+01
99i0qiw53bd6bmmd8g6m7x0p7sjwm0sa	NTM0YTZhODY3MDU3MTA4OWU1ZTQ4ZDM0ZjQ2YjkwZDc1Njc1YzdjNjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4MDdjMjk4MzI1OGU5Mzg0MGQzYWRhZGUwMjQ1MTFhOTJiMGQzZDZmIn0=	2015-12-12 17:25:12.812666+01
gs8ayemn0kafvaf7bym8qolbmid0mxcw	MTY1YmU2YzE1MDA2MDYxZjkxNjNkZTlkNzFjNGJlN2JlMjQ2ZjNkZjp7Il9hdXRoX3VzZXJfaGFzaCI6IjgwN2MyOTgzMjU4ZTkzODQwZDNhZGFkZTAyNDUxMWE5MmIwZDNkNmYiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-12 17:26:48.588465+01
mazqhvw19ut4xqxwoc280mv9rre2y2lj	MTY1YmU2YzE1MDA2MDYxZjkxNjNkZTlkNzFjNGJlN2JlMjQ2ZjNkZjp7Il9hdXRoX3VzZXJfaGFzaCI6IjgwN2MyOTgzMjU4ZTkzODQwZDNhZGFkZTAyNDUxMWE5MmIwZDNkNmYiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-12 17:26:49.968733+01
8jt464tmnpxz5log7k9ad4lqttk0l8ic	MTY1YmU2YzE1MDA2MDYxZjkxNjNkZTlkNzFjNGJlN2JlMjQ2ZjNkZjp7Il9hdXRoX3VzZXJfaGFzaCI6IjgwN2MyOTgzMjU4ZTkzODQwZDNhZGFkZTAyNDUxMWE5MmIwZDNkNmYiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-12 17:27:03.014813+01
pemzblq3od8kt2t91ltbj8fh6918t8ql	ZGYyM2E3YmZhOTA1MThmOWZhMzFkMTVjMTI1MzUwOTYwNzY4N2JjYjp7Il9hdXRoX3VzZXJfaGFzaCI6IjBmMTM2MDlmNTg1YjhiYjdkZGIyZTE0YWJlYzE3MzZjNzZjZWJlNjkiLCJfYXV0aF91c2VyX2lkIjoiMiIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=	2015-12-12 17:27:50.314962+01
\.


--
-- Data for Name: scipost_authorreply; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_authorreply (id, status, reply_text, date_submitted, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, author_id, commentary_id, in_reply_to_comment_id, in_reply_to_report_id, submission_id) FROM stdin;
\.


--
-- Name: scipost_authorreply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_authorreply_id_seq', 1, false);


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
\.


--
-- Name: scipost_comment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_comment_id_seq', 1, false);


--
-- Data for Name: scipost_commentary; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentary (id, vetted, type, open_for_commenting, pub_title, arxiv_link, "pub_DOI_link", author_list, pub_date, pub_abstract, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, latest_activity, vetted_by_id) FROM stdin;
\.


--
-- Name: scipost_commentary_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentary_id_seq', 1, false);


--
-- Data for Name: scipost_commentaryrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentaryrating (id, clarity, correctness, usefulness, commentary_id, rater_id) FROM stdin;
\.


--
-- Name: scipost_commentaryrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentaryrating_id_seq', 1, false);


--
-- Data for Name: scipost_commentrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_commentrating (id, clarity, correctness, usefulness, comment_id, rater_id) FROM stdin;
\.


--
-- Name: scipost_commentrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_commentrating_id_seq', 1, false);


--
-- Data for Name: scipost_contributor; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_contributor (id, rank, title, orcid_id, affiliation, address, personalwebpage, nr_reports, report_clarity_rating, report_correctness_rating, report_usefulness_rating, nr_comments, comment_clarity_rating, comment_correctness_rating, comment_usefulness_rating, user_id) FROM stdin;
1	5	PR		test1			0	0	0	0	0	0	0	0	2
\.


--
-- Name: scipost_contributor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_contributor_id_seq', 1, true);


--
-- Data for Name: scipost_report; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_report (id, status, qualification, strengths, weaknesses, report, requested_changes, recommendation, date_invited, date_submitted, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, author_id, invited_by_id, submission_id) FROM stdin;
\.


--
-- Name: scipost_report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_report_id_seq', 1, false);


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

COPY scipost_submission (id, vetted, submitted_to_journal, domain, specialization, status, open_for_reporting, open_for_commenting, title, author_list, abstract, arxiv_link, submission_date, nr_ratings, clarity_rating, correctness_rating, usefulness_rating, latest_activity, editor_in_charge_id, submitted_by_id) FROM stdin;
\.


--
-- Name: scipost_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_submission_id_seq', 1, false);


--
-- Data for Name: scipost_submissionrating; Type: TABLE DATA; Schema: public; Owner: scipostv1db
--

COPY scipost_submissionrating (id, clarity, correctness, usefulness, rater_id, submission_id) FROM stdin;
\.


--
-- Name: scipost_submissionrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: scipostv1db
--

SELECT pg_catalog.setval('scipost_submissionrating_id_seq', 1, false);


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
-- Name: django_content_type_app_label_561bc37e5a6ea6ea_uniq; Type: CONSTRAINT; Schema: public; Owner: scipostv1db; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_561bc37e5a6ea6ea_uniq UNIQUE (app_label, model);


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
-- Name: auth_group_name_22300af083d055a4_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_group_name_22300af083d055a4_like ON auth_group USING btree (name varchar_pattern_ops);


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
-- Name: auth_user_username_3eb7429306e522bc_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX auth_user_username_3eb7429306e522bc_like ON auth_user USING btree (username varchar_pattern_ops);


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
-- Name: django_session_session_key_23a16fd1e8e217c5_like; Type: INDEX; Schema: public; Owner: scipostv1db; Tablespace: 
--

CREATE INDEX django_session_session_key_23a16fd1e8e217c5_like ON django_session USING btree (session_key varchar_pattern_ops);


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
-- Name: auth_content_type_id_19a11dbb5cf64c6d_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_content_type_id_19a11dbb5cf64c6d_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group__permission_id_13f0192df91ada6_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group__permission_id_13f0192df91ada6_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissio_group_id_44476e2990c289c6_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_group_id_44476e2990c289c6_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user__permission_id_225af1e608c39bb2_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user__permission_id_225af1e608c39bb2_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups_group_id_96e306a34b1fdde_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_96e306a34b1fdde_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups_user_id_38eb384af7fe4ced_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_38eb384af7fe4ced_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permiss_user_id_19782b049daf6389_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permiss_user_id_19782b049daf6389_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: djan_content_type_id_7a0682f1585530f1_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT djan_content_type_id_7a0682f1585530f1_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_51c000be9563163e_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_51c000be9563163e_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: editor_in_charge_id_678a982160ec7de7_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submission
    ADD CONSTRAINT editor_in_charge_id_678a982160ec7de7_fk_scipost_contributor_id FOREIGN KEY (editor_in_charge_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: s_in_reply_to_comment_id_3ab38b881664c5fd_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT s_in_reply_to_comment_id_3ab38b881664c5fd_fk_scipost_comment_id FOREIGN KEY (in_reply_to_comment_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sci_in_reply_to_report_id_353d61599149b4eb_fk_scipost_report_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT sci_in_reply_to_report_id_353d61599149b4eb_fk_scipost_report_id FOREIGN KEY (in_reply_to_report_id) REFERENCES scipost_report(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scip_submitted_by_id_49da9cc433ba31f9_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submission
    ADD CONSTRAINT scip_submitted_by_id_49da9cc433ba31f9_fk_scipost_contributor_id FOREIGN KEY (submitted_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipos_invited_by_id_5f7fd99819bf5dbd_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipos_invited_by_id_5f7fd99819bf5dbd_fk_scipost_contributor_id FOREIGN KEY (invited_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_au_author_id_7ff889415a3cca77_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_au_author_id_7ff889415a3cca77_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_aut_rater_id_5f46bad82eac1f28_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreplyrating
    ADD CONSTRAINT scipost_aut_rater_id_5f46bad82eac1f28_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_aut_reply_id_6510820350c6f14a_fk_scipost_authorreply_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreplyrating
    ADD CONSTRAINT scipost_aut_reply_id_6510820350c6f14a_fk_scipost_authorreply_id FOREIGN KEY (reply_id) REFERENCES scipost_authorreply(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_c_in_reply_to_id_44f130e7bf022adb_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_c_in_reply_to_id_44f130e7bf022adb_fk_scipost_comment_id FOREIGN KEY (in_reply_to_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_co_author_id_452160c42696cf47_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_co_author_id_452160c42696cf47_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_com_rater_id_1c565adb8105debc_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentrating
    ADD CONSTRAINT scipost_com_rater_id_1c565adb8105debc_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_com_rater_id_6b0e2ce2e0ad8566_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentaryrating
    ADD CONSTRAINT scipost_com_rater_id_6b0e2ce2e0ad8566_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_comme_comment_id_5171e8e38a3b993d_fk_scipost_comment_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentrating
    ADD CONSTRAINT scipost_comme_comment_id_5171e8e38a3b993d_fk_scipost_comment_id FOREIGN KEY (comment_id) REFERENCES scipost_comment(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_14778ec647655bd8_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_commentary_id_14778ec647655bd8_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_6dfefeacac103e0f_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentaryrating
    ADD CONSTRAINT scipost_commentary_id_6dfefeacac103e0f_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_commentary_id_78decc5c7941ce0a_fk_scipost_commentary_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_commentary_id_78decc5c7941ce0a_fk_scipost_commentary_id FOREIGN KEY (commentary_id) REFERENCES scipost_commentary(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_contributor_user_id_27b45ca802c0d3bc_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_contributor
    ADD CONSTRAINT scipost_contributor_user_id_27b45ca802c0d3bc_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_re_author_id_277db53186193bb8_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_re_author_id_277db53186193bb8_fk_scipost_contributor_id FOREIGN KEY (author_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_repo_rater_id_9460c7f3c896053_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_reportrating
    ADD CONSTRAINT scipost_repo_rater_id_9460c7f3c896053_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_reportr_report_id_34a74ecc347d1c85_fk_scipost_report_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_reportrating
    ADD CONSTRAINT scipost_reportr_report_id_34a74ecc347d1c85_fk_scipost_report_id FOREIGN KEY (report_id) REFERENCES scipost_report(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_sub_rater_id_54c21bbfd8bef5a8_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submissionrating
    ADD CONSTRAINT scipost_sub_rater_id_54c21bbfd8bef5a8_fk_scipost_contributor_id FOREIGN KEY (rater_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_17789c9872948123_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_submissionrating
    ADD CONSTRAINT scipost_submission_id_17789c9872948123_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_461b50e51cabda75_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_report
    ADD CONSTRAINT scipost_submission_id_461b50e51cabda75_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_5f122cf066fa25ea_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_authorreply
    ADD CONSTRAINT scipost_submission_id_5f122cf066fa25ea_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_submission_id_7559e84a23dbf4b4_fk_scipost_submission_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_comment
    ADD CONSTRAINT scipost_submission_id_7559e84a23dbf4b4_fk_scipost_submission_id FOREIGN KEY (submission_id) REFERENCES scipost_submission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scipost_vetted_by_id_1ddf21ddd805a269_fk_scipost_contributor_id; Type: FK CONSTRAINT; Schema: public; Owner: scipostv1db
--

ALTER TABLE ONLY scipost_commentary
    ADD CONSTRAINT scipost_vetted_by_id_1ddf21ddd805a269_fk_scipost_contributor_id FOREIGN KEY (vetted_by_id) REFERENCES scipost_contributor(id) DEFERRABLE INITIALLY DEFERRED;


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

