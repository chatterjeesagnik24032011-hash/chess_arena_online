CREATE FUNCTION public.find_or_join_random_game(
    p_minutes integer DEFAULT 10,
    p_increment integer DEFAULT 0
)
RETURNS TABLE (
    game_id uuid,
    color text,
    game_status text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id uuid;
    v_game_id uuid;
    v_color text;
    v_status text;
    v_seconds integer;
BEGIN
    -- Get logged-in user
    v_user_id := auth.uid();

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'You must be logged in.';
    END IF;

    -- Safety values
    IF p_minutes IS NULL OR p_minutes < 1 THEN
        p_minutes := 10;
    END IF;

    IF p_increment IS NULL OR p_increment < 0 THEN
        p_increment := 0;
    END IF;

    v_seconds := p_minutes * 60;

    -- =====================================================
    -- FIND AN EXISTING WAITING PLAYER
    -- =====================================================

    SELECT g.id
    INTO v_game_id
    FROM public.games AS g
    WHERE g.status = 'waiting'
      AND g.white_id IS NOT NULL
      AND g.black_id IS NULL
      AND g.white_id <> v_user_id
      AND g.white_time = v_seconds
      AND g.increment = p_increment
    ORDER BY g.created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    -- =====================================================
    -- JOIN EXISTING GAME AS BLACK
    -- =====================================================

    IF v_game_id IS NOT NULL THEN

        UPDATE public.games AS g
        SET
            black_id = v_user_id,
            black_time = v_seconds,
            status = 'active',
            white_confirmed = false,
            black_confirmed = false,
            updated_at = now()
        WHERE g.id = v_game_id;

        v_color := 'b';
        v_status := 'active';

        RETURN QUERY
        SELECT
            v_game_id,
            v_color,
            v_status;

        RETURN;
    END IF;

    -- =====================================================
    -- NO PLAYER FOUND
    -- CREATE WAITING GAME AS WHITE
    -- =====================================================

    INSERT INTO public.games (
        white_id,
        black_id,
        status,
        fen,
        moves,
        white_time,
        black_time,
        increment,
        white_confirmed,
        black_confirmed,
        created_at,
        updated_at
    )
    VALUES (
        v_user_id,
        NULL,
        'waiting',
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
        '[]'::jsonb,
        v_seconds,
        v_seconds,
        p_increment,
        false,
        false,
        now(),
        now()
    )
    RETURNING id INTO v_game_id;

    v_color := 'w';
    v_status := 'waiting';

    RETURN QUERY
    SELECT
        v_game_id,
        v_color,
        v_status;

END;
$$;

GRANT EXECUTE
ON FUNCTION public.find_or_join_random_game(integer, integer)
TO authenticated;
