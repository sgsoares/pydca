from pydca.plmdca import plmdca 
from pydca.sequence_backmapper.sequence_backmapper import SequenceBackmapper
from pydca.fasta_reader.fasta_reader import get_alignment_from_fasta_file
from pydca.dca_utilities import dca_utilities
from argparse import ArgumentParser
import logging
import sys
import os


"""Top level module for plmDCA. Defines command line interface and 
configures logging.

Author: Mehari B. Zerihun
"""

def configure_logging():
    """Configures logging. When configured, the logging level is INFO and
    messages are logged to stream handler. Log level name are colored whenever
    the terminal supports that. INFO level is Green, WARNING level is Yellow and
    ERROR level is Red.
    """
    from pydca.config_dca.config_log import LOGGING_CONFIG
    from pydca.config_dca.config_log import ConsoleColor as c_color
    import logging.config

    logging.config.dictConfig(LOGGING_CONFIG)
    logging.addLevelName(logging.INFO, '{}{}{}'.format(
        c_color.green, logging.getLevelName(logging.INFO), c_color.nocolor))
    logging.addLevelName(logging.WARNING, '{}{}{}'.format(
        c_color.yellow, logging.getLevelName(logging.WARNING), c_color.nocolor))
    logging.addLevelName(logging.ERROR, '{}{}{}'.format(
        c_color.red, logging.getLevelName(logging.ERROR), c_color.nocolor))
    return None


class CmdArgs:
    """Defines command line argument variables for plmDCA.
    """

    subcommand_name = 'subcommand_name'
    msa_file = 'msa_file'
    msa_file_help = """Multiple sequence alignment (MSA) file in FASTA format.
    """
    biomolecule = 'biomolecule'
    biomolecule_help = """Type of biomolecule. It should be either protein or RNA 
    in lower or upper case letters.
    """
    refseq_file_optional = '--refseq_file'
    refseq_file_help = """FASTA formatted file containing a reference sequence.
    The reference sequence should not contain gaps or non-standard residues.
    """
    verbose_optional = '--verbose'
    verbose_optional_help = """Show logging information on the terminal.
    """
    apc_optional = '--apc'
    apc_help = """Compute the average product corrected (APC) DCA score.
    """
    subcommand_name_help = """Subcommands destination
    """
    seqid_optional = '--seqid'
    seqid_optional_help = """Cut-off value of sequences similarity above which they
    are lumped together.
    """
    lambda_h_optional = '--lambda_h'
    lambda_h_optional_help = """Value of fields penalizing constant for L2 
    regularization of fields.
    """
    lambda_J_optional = '--lambda_J'
    lambda_J_optional_help = """Value of couplings penalizing constant for L2 
    regularization of couplings.
    """
    num_iterations_optional = '--num_iterations'
    num_iterations_help = """Number of iterations for gradient decent 
    for negative pseudolikelihood minimization.
    """
    output_dir_optional = '--output_dir'
    output_dir_help = """Directory path to which output results are written.
    If the directory is not existing, it will be created provided that the user
    has a privilege to do so. If this path is not provided, an output directory
    is created using the base name of the MSA file, with a prefix and/or postfix
    added to it.
    """
# end of class CmdArgs 


def get_plmdca_inst(biomolecule, msa_file, seqid=None, lambda_h=None, lambda_J=None, 
        num_iterations=None):
    """Creates a PlmDCA instance and returns it.

    Parameters
    ----------
        msa_file : str 
            Path to FASTA formatted MSA file.
        biomolecule : str
            Type of biomolecule the MSA data represents.
        seqid : float
            Sequences identity cut-off value.
        lambda_h : float 
            Value of fileds penalizing constant. 
        lambda_J : float
            Value of couplings penalizing constant. 
        num_iter_steps : int 
            Number of iteration for gradient decent.

    Returns
    ------- 
        plmdca_inst : PlmDCA 
            An instance of PlmDCA class
    """
    plmdca_inst = plmdca.PlmDCA(biomolecule, msa_file, 
        seqid=seqid, lambda_h=lambda_h, 
        lambda_J=lambda_J, num_iterations = num_iterations,
    )
    return plmdca_inst 


def execute_from_command_line(biomolecule, msa_file, the_command = None, 
    refseq_file = None, seqid = None, lambda_h = None, lambda_J = None, 
    num_iterations = None,  apc = False ,verbose = False, output_dir = None):
    """Runs plmdca computation from the command line.

    Parameters
    ----------
        biomolecule : str
            Type of biomolecule the MSA data represents.
        msa_file : str 
            Path to FASTA formatted MSA file.
        the_command : str
            Name of subcommand for plmDCA
        refseq_file: str
            Path to reference sequence file
        seqid : float
            Sequences identity cut-off value.
        lambda_h : float 
            Value of fileds penalizing constant. 
        lambda_J : float
            Value of couplings penalizing constant. 
        num_iterations : int 
            Number of iteration for gradient decent.
        apc : bool
            Perform average product correction to DCA scores. 
        verbose : bool 
            True or False. Determines if plmdca computation is done in verbose mode or not.
        output_dir : str    
            Directory where computed results are to be saved in. 
    """

    if verbose : configure_logging()
    
    plmdca_instance = get_plmdca_inst(biomolecule, msa_file, seqid=seqid, 
        lambda_h=lambda_h, lambda_J=lambda_J, num_iterations = num_iterations
    )

# compute Frobenius norm of couplings
    if the_command=='compute_fn':
        #create path to output directory is not supplied by user
        if not output_dir:
            msa_file_base_name, ext = os.path.splitext(os.path.basename(msa_file))
            output_dir = 'PLMDCA_output_' + msa_file_base_name
        #create dca coutput directory
        dca_utilities.create_directories(output_dir)
        param_metadata = dca_utilities.plmdca_param_metadata(plmdca_instance)
        mapped_sites = None
        if refseq_file:# do backmapping when reference sequence file is provided
            seq_backmapper = SequenceBackmapper(
                msa_file = msa_file,
                refseq_file = refseq_file,
                biomolecule = plmdca_instance.biomolecule)
            mapped_sites = seq_backmapper.map_to_reference_sequence()
        if apc:
            score_type = 'PLMDCA Frobenius norm, average product corrected (APC)'
            sorted_FN = plmdca_instance.compute_sorted_FN_APC()
            fn_file_path = dca_utilities.get_dca_output_file_path(output_dir,
                msa_file, prefix = 'PLMDCA_apc_fn_scores_', postfix='.txt'
            )
        else:
            score_type = 'PLDCA Frobenius norm, non-APC (not average product corrected)'
            sorted_FN = plmdca_instance.compute_sorted_FN()
            fn_file_path = dca_utilities.get_dca_output_file_path(output_dir,
                msa_file, prefix = 'PLMDCA_raw_fn_scores_', postfix='.txt'
            )
        dca_utilities.write_sorted_dca_scores(fn_file_path, sorted_FN,
            site_mapping = mapped_sites, metadata = param_metadata,
            score_type = score_type
        )    
    return None 


def run_plm_dca():
    """Performs plmDCA computation based on argument passed from the command line. 
    """
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest = CmdArgs.subcommand_name)
    parser_compute_fn = subparsers.add_parser('compute_fn', help='computes the Frobenius norm of couplings.')
    parser_compute_fn.add_argument(CmdArgs.biomolecule, help=CmdArgs.biomolecule_help)
    parser_compute_fn.add_argument(CmdArgs.msa_file, help=CmdArgs.msa_file_help)
    parser_compute_fn.add_argument(CmdArgs.seqid_optional, help=CmdArgs.seqid_optional_help, type=float)
    parser_compute_fn.add_argument(CmdArgs.lambda_h_optional, help=CmdArgs.lambda_h_optional_help, type=float)
    parser_compute_fn.add_argument(CmdArgs.lambda_J_optional, help=CmdArgs.lambda_J_optional_help, type=float)
    parser_compute_fn.add_argument(CmdArgs.num_iterations_optional, help=CmdArgs.num_iterations_help, type=int)
    parser_compute_fn.add_argument(CmdArgs.refseq_file_optional, help=CmdArgs.refseq_file_help)
    parser_compute_fn.add_argument(CmdArgs.verbose_optional, help=CmdArgs.verbose_optional_help, action='store_true')
    parser_compute_fn.add_argument(CmdArgs.apc_optional, help=CmdArgs.apc_help, action='store_true')
    parser_compute_fn.add_argument(CmdArgs.output_dir_optional, help=CmdArgs.output_dir_help)
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    args_dict = vars(args)

    execute_from_command_line(args_dict.get('biomolecule'),args_dict.get('msa_file'),
        the_command = args_dict.get('subcommand_name'),
        refseq_file = args_dict.get('refseq_file'), 
        seqid=args_dict.get('seqid'),
        lambda_h=args_dict.get('lambda_h'),
        lambda_J = args_dict.get('lambda_J'),
        num_iterations = args_dict.get('num_iterations'),
        apc = args_dict.get('apc'),
        output_dir = args_dict.get('output_dir'),
        verbose = args_dict.get('verbose'),
    )
    return None 

if __name__ == "__main__":
    """
    """
    run_plm_dca()