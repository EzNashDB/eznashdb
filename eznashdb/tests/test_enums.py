from eznashdb.enums import RelativeSize, SeeHearScore


def describe_relative_size():
    """Tests for RelativeSize enum display methods"""

    def test_get_display_returns_label_without_badge():
        """Test that get_display returns only the label text"""
        size = RelativeSize.L
        result = size.get_display()

        # Should contain the label
        assert "Equal or larger than men's" in result
        # Should not contain a badge
        assert "badge" not in result.lower()

    def test_get_option_display_returns_badge_and_label():
        """Test that get_option_display returns both badge and label"""
        size = RelativeSize.S
        result = size.get_option_display()

        # Should contain the badge
        assert "badge" in result
        assert ">S<" in result
        # Should contain the label
        assert "Less than half men's size" in result

    def test_get_display_choices_uses_option_display():
        """Test that get_display_choices uses get_option_display for rendering"""
        choices = RelativeSize.get_display_choices()

        # Should have all enum values
        assert len(choices) == len(RelativeSize)

        # Each choice should use get_option_display (contains badge)
        for value, display in choices:
            assert "badge" in display
            # Value should match an enum value
            assert value in [choice.value for choice in RelativeSize]

    def test_get_display_choices_with_blank():
        """Test that get_display_choices includes blank option when requested"""
        choices = RelativeSize.get_display_choices(include_blank=True)

        # Should have all enum values plus blank
        assert len(choices) == len(RelativeSize) + 1
        # First choice should be blank
        assert choices[0] == ("", "-------")


def describe_see_hear_score():
    """Tests for SeeHearScore enum display methods"""

    def test_get_display_returns_stars_only():
        """Test that get_display returns only stars without number"""
        score = SeeHearScore._5
        result = score.get_display()

        # Should contain star icons
        assert "fa-star" in result
        # Should not contain a badge
        assert "badge" not in result.lower()

    def test_get_option_display_returns_badge_and_stars():
        """Test that get_option_display returns both badge and stars"""
        score = SeeHearScore._4
        result = score.get_option_display()

        # Should contain the badge
        assert "badge" in result
        assert ">4<" in result
        # Should contain star icons
        assert "fa-star" in result

    def test_get_display_star_count():
        """Test that get_display renders correct number of stars"""
        for score in SeeHearScore:
            result = score.get_display()
            score_value = int(score.value)
            # Count filled stars (fa-solid icons)
            filled_stars = result.count("fa-solid")
            assert filled_stars == score_value

    def test_get_display_choices_uses_option_display():
        """Test that get_display_choices uses get_option_display for rendering"""
        choices = SeeHearScore.get_display_choices()

        # Should have all enum values
        assert len(choices) == len(SeeHearScore)

        # Each choice should use get_option_display (contains badge and stars)
        for value, display in choices:
            assert "badge" in display
            assert "fa-star" in display
            # Value should match an enum value
            assert value in [choice.value for choice in SeeHearScore]

    def test_get_display_choices_with_blank():
        """Test that get_display_choices includes blank option when requested"""
        choices = SeeHearScore.get_display_choices(include_blank=True)

        # Should have all enum values plus blank
        assert len(choices) == len(SeeHearScore) + 1
        # First choice should be blank
        assert choices[0] == ("", "-------")
