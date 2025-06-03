--
-- PostgreSQL database dump
--

-- Dumped from database version 16.0
-- Dumped by pg_dump version 16.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: unauthorized_exits; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unauthorized_exits (
    id integer NOT NULL,
    vehicle_id character varying(50),
    reason text,
    plate_number character varying(10) NOT NULL,
    exit_time timestamp without time zone NOT NULL,
    gate_location character varying(10) NOT NULL
);


ALTER TABLE public.unauthorized_exits OWNER TO postgres;

--
-- Name: unauthorized_exits_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unauthorized_exits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unauthorized_exits_id_seq OWNER TO postgres;

--
-- Name: unauthorized_exits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unauthorized_exits_id_seq OWNED BY public.unauthorized_exits.id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vehicles (
    id integer NOT NULL,
    license_plate character varying(20),
    entry_time timestamp without time zone,
    exit_time timestamp without time zone,
    is_unauthorized boolean DEFAULT false,
    plate_number text,
    payment_status integer,
    payment_amount numeric,
    payment_time timestamp without time zone
);


ALTER TABLE public.vehicles OWNER TO postgres;

--
-- Name: vehicles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vehicles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vehicles_id_seq OWNER TO postgres;

--
-- Name: vehicles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vehicles_id_seq OWNED BY public.vehicles.id;


--
-- Name: unauthorized_exits id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unauthorized_exits ALTER COLUMN id SET DEFAULT nextval('public.unauthorized_exits_id_seq'::regclass);


--
-- Name: vehicles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles ALTER COLUMN id SET DEFAULT nextval('public.vehicles_id_seq'::regclass);


--
-- Data for Name: unauthorized_exits; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.unauthorized_exits (id, vehicle_id, reason, plate_number, exit_time, gate_location) FROM stdin;
1	\N	\N	RAD667J	2025-06-03 11:25:29.092372	Unknown
2	\N	\N	RAD667J	2025-06-03 11:40:24.9168	Unknown
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vehicles (id, license_plate, entry_time, exit_time, is_unauthorized, plate_number, payment_status, payment_amount, payment_time) FROM stdin;
1	\N	2025-06-02 15:08:19.892798	2025-06-02 17:12:53.79661	f	RAD667J	1	1000	2025-06-02 17:08:22.41676
2	\N	2025-06-03 11:23:18.758424	\N	f	RAD667J	0	\N	\N
3	\N	2025-06-03 11:38:50.2934	2025-06-03 11:51:57.384536	f	RAD667J	1	500	2025-06-03 11:49:14.96148
\.


--
-- Name: unauthorized_exits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.unauthorized_exits_id_seq', 2, true);


--
-- Name: vehicles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vehicles_id_seq', 3, true);


--
-- Name: unauthorized_exits unauthorized_exits_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unauthorized_exits
    ADD CONSTRAINT unauthorized_exits_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

