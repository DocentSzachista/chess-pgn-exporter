import chess.pgn
from collections import defaultdict
import io
import re

class AbsentHeaderException(Exception):
    """Called when not all PGN headers has been provided"""
    pass
    
class ChessGame():
    """Class to handle PGN export."""
    def __init__(self) -> None:
        self.moves_exporter =  chess.pgn.StringExporter(headers= False, variations=True, comments=True)
        self.required_headers = ["Event", "Site", "Date", "Round", "White", "Black", "Result", "Opening"]
        self.lichess_study_pattern = re.compile(r'^[^:]+(?=:)')
        
    def __validate_pgn(self, game: chess.pgn.Game):
        """
            Simple PGN tag validation. Checks if the required headers are present.
        """
        missing_headers = []
        for header in self.required_headers:
            if header not in game.headers:
                missing_headers.append(header)
        if len(missing_headers) != 0: 
            raise AbsentHeaderException(f"There are missing headers: {str(missing_headers)}")
    
    def __convert_pgn(self, pgn_notation: str):
        """Converts pgn to dict."""
        streaming_object = io.StringIO(pgn_notation)
        game = chess.pgn.read_game(streaming_object)
        self.__validate_pgn(game)
        game_dict = {  
            header: game.headers.get(header, "") for header in self.required_headers
        }
        game_dict['moves'] = game.accept(self.moves_exporter)

        return game_dict
    
    def __group_studies_lichess(self, games: list):
        """Detect studies and group games by studies."""
        studies = defaultdict(list)
        for game in games:
            match = self.lichess_study_pattern.search(game['Event'])
            if match:
                study = match.group(0)
                game['Event'].replace(study, "")
                studies[study].append(game)
        return studies
    
    def import_user_lichess(self, pgn_list: list ):
        all_games = [
            self.__convert_pgn(pgn) for pgn in pgn_list
        ]
        return self.__group_studies_lichess(all_games)

    def import_user_pgn(self, pgn: str):
        # TODO: maybe add validation if there are more than one PGNs from file retrieved. 
        return self.__convert_pgn(pgn)
