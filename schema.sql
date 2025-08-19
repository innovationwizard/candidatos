--
-- PostgreSQL database dump
--

\restrict N4DlEvFJKqNEc8uAMEE2beqgKhwNiVHFtZkdNg1zZ0cQ4HipjgTa4xJ8oqkkxpX

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Homebrew)

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
-- Name: metadata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.metadata (
    metadata_id integer NOT NULL,
    mesa integer,
    tipo text,
    padron integer,
    validos integer,
    nulos integer,
    en_blanco integer,
    emitidos integer,
    invalidos integer,
    total integer,
    impugnaciones integer,
    papeletas_recibidas integer,
    papeletas_no_usadas integer,
    validos_calculado integer,
    emitidos_calculado integer,
    total_calculado integer
);


ALTER TABLE public.metadata OWNER TO postgres;

--
-- Name: metadata_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.metadata_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.metadata_metadata_id_seq OWNER TO postgres;

--
-- Name: metadata_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.metadata_metadata_id_seq OWNED BY public.metadata.metadata_id;


--
-- Name: partido; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partido (
    partido_id integer NOT NULL,
    partido_name text
);


ALTER TABLE public.partido OWNER TO postgres;

--
-- Name: partido_partido_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partido_partido_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partido_partido_id_seq OWNER TO postgres;

--
-- Name: partido_partido_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partido_partido_id_seq OWNED BY public.partido.partido_id;


--
-- Name: ubis; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ubis (
    mesa integer NOT NULL,
    dept_name text,
    dept_id text,
    muni_name text,
    muni_id text,
    cdev text
);


ALTER TABLE public.ubis OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    username text NOT NULL,
    password text NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: voto; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.voto (
    voto_id integer NOT NULL,
    mesa integer,
    tipo text,
    partido_id integer,
    voto integer
);


ALTER TABLE public.voto OWNER TO postgres;

--
-- Name: voto_voto_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.voto_voto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.voto_voto_id_seq OWNER TO postgres;

--
-- Name: voto_voto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.voto_voto_id_seq OWNED BY public.voto.voto_id;


--
-- Name: metadata metadata_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata ALTER COLUMN metadata_id SET DEFAULT nextval('public.metadata_metadata_id_seq'::regclass);


--
-- Name: partido partido_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partido ALTER COLUMN partido_id SET DEFAULT nextval('public.partido_partido_id_seq'::regclass);


--
-- Name: voto voto_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voto ALTER COLUMN voto_id SET DEFAULT nextval('public.voto_voto_id_seq'::regclass);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (metadata_id);


--
-- Name: partido partido_partido_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partido
    ADD CONSTRAINT partido_partido_name_key UNIQUE (partido_name);


--
-- Name: partido partido_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partido
    ADD CONSTRAINT partido_pkey PRIMARY KEY (partido_id);


--
-- Name: ubis ubis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ubis
    ADD CONSTRAINT ubis_pkey PRIMARY KEY (mesa);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (username);


--
-- Name: voto voto_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voto
    ADD CONSTRAINT voto_pkey PRIMARY KEY (voto_id);


--
-- Name: metadata metadata_mesa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metadata
    ADD CONSTRAINT metadata_mesa_fkey FOREIGN KEY (mesa) REFERENCES public.ubis(mesa) DEFERRABLE;


--
-- Name: voto voto_mesa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voto
    ADD CONSTRAINT voto_mesa_fkey FOREIGN KEY (mesa) REFERENCES public.ubis(mesa) DEFERRABLE;


--
-- Name: voto voto_partido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voto
    ADD CONSTRAINT voto_partido_id_fkey FOREIGN KEY (partido_id) REFERENCES public.partido(partido_id) DEFERRABLE;


--
-- PostgreSQL database dump complete
--

\unrestrict N4DlEvFJKqNEc8uAMEE2beqgKhwNiVHFtZkdNg1zZ0cQ4HipjgTa4xJ8oqkkxpX

